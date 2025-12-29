from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosNarrativeORM, CaosNarrativeVersionORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_narrative import CreateNarrativeUseCase
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Application.get_narrative_details import GetNarrativeDetailsUseCase
from src.WorldManagement.Caos.Application.get_world_narratives import GetWorldNarrativesUseCase
from src.FantasyWorld.Domain.Services.NarrativeService import NarrativeService
from .view_utils import resolve_jid_orm, check_world_access, get_admin_status

@csrf_exempt
@require_POST
@login_required
def import_narrative_file(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo.'}, status=400)
        
        text = NarrativeService.import_text(request.FILES['file'])
        return JsonResponse({'success': True, 'text': text})

    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error interno: {str(e)}"}, status=500)

# Removed local resolve_jid, using resolve_jid_orm instead

from django.http import Http404

def ver_narrativa_mundo(request, jid):
    try: 
        repo = DjangoCaosRepository()
        
        # Visibility Check
        w = resolve_jid_orm(jid)
        if not w:
             messages.error(request, f"Mundo no encontrado: {jid}")
             return redirect('home')
             
        can_access, _ = check_world_access(request, w)
        if not can_access:
            return render(request, 'private_access.html', status=403)
            
        real_jid = w.id if w else jid
        
        # PERIOD SUPPORT
        period_slug = request.GET.get('period', 'actual')
        
        context = GetWorldNarrativesUseCase(repo).execute(real_jid, request.user, period_slug=period_slug)
        
        if not context: 
            print(f"❌ Mundo no encontrado para JID: {jid}")
            messages.error(request, f"Mundo no encontrado: {jid}")
            return redirect('home')
        
        context['current_period_slug'] = period_slug
        return render(request, 'indice_narrativa.html', context)
    except Exception as e: 
        print(f"❌ Error en ver_narrativa_mundo: {e}")
        messages.error(request, f"Error al cargar narrativas: {e}")
        return redirect('home')

def leer_narrativa(request, nid):
    try:
        repo = DjangoCaosRepository()
        
        # Visibility Check (via Narrative -> World)
        # We need the narrative ORM to check world status
        try:
            n_orm = CaosNarrativeORM.objects.get(public_id=nid)
        except:
            n_orm = CaosNarrativeORM.objects.filter(nid=nid).first()

        if n_orm:
           can_access, is_author_or_team = check_world_access(request, n_orm.world)
           if not can_access:
               return render(request, 'private_access.html', status=403)

        context = GetNarrativeDetailsUseCase(repo).execute(nid, request.user)
        
        if context:
           is_admin, is_team_member = get_admin_status(request.user)
           # is_author_or_team from check_world_access is more robust for editing
           context['is_author'] = is_author_or_team or is_team_member
           context['allow_proposals'] = is_team_member
           context['is_admin_role'] = is_admin
           
           # CHECK FOR DRAFTS (Phase 3)
           if request.user.is_authenticated:
               draft = CaosNarrativeVersionORM.objects.filter(
                   narrative=n_orm, 
                   author=request.user, 
                   status='DRAFT'
               ).first()
               if draft:
                   context['has_draft'] = True
                   context['draft_version'] = draft

        if not context:
            messages.error(request, f"No se encontró la narrativa: {nid}")
            return redirect('home')

        # RETOUCH LOGIC: Pre-fill with rejected draft if requested
        src_version_id = request.GET.get('src_version')
        if src_version_id and context.get('narr'):
            try:
                v_src = CaosNarrativeVersionORM.objects.get(id=src_version_id)
                # Check match (Robust NID comparison)
                target_nid = getattr(context['narr'], 'nid', None) or getattr(context['narr'], 'id', None)
                if target_nid and v_src.narrative.nid == target_nid:
                     # SECURITY & UX: If I own this draft OR AM ADMIN, I must be allowed to edit it
                     # Use IDs for safer comparison
                     is_owner = (v_src.author and request.user.id == v_src.author.id)
                     is_admin = context.get('is_admin_role', False)
                     
                     if is_owner or request.user.is_superuser or is_admin:
                         context['is_author'] = True 
                         context['allow_proposals'] = True
                         context['open_editor_auto'] = True
                         context['is_retouch_mode'] = True # New flag for UI
                         context['hide_navigation'] = True # Disable nav as requested

                     context['narr'].titulo = v_src.proposed_title
                     context['narr'].contenido = v_src.proposed_content
                     messages.info(request, f"✏️ Retomando borrador rechazado v{v_src.version_number}. Edita y vuelve a enviar.")
            except Exception as e:
                print(f"Error loading src_version (Narrative): {e}")

        return render(request, 'visor_narrativa.html', context)
    except Exception as e:
        print(f"❌ Error al leer narrativa '{nid}': {e}")
        messages.error(request, f"Error interno al leer narrativa: {nid}")
        return redirect('home')

@login_required
def editar_narrativa(request, nid):
    # Lock Check
    try: n_orm = CaosNarrativeORM.objects.get(nid=nid) # Try internal ID first usually stored in logic, but here assume external input
    except: 
       try: n_orm = CaosNarrativeORM.objects.get(public_id=nid)
       except: n_orm = None
    
    if n_orm:
        # --- SECURITY CHECK ---
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        try:
             # Check ownership of the NARRATIVE (created_by) or the WORLD owner
             # If strict direct ownership means "World Owner controls all", check world.
             # Usually narr author can edit their own narr.
             # check_ownership supports 'created_by'.
             check_ownership(request.user, n_orm)
        except:
             messages.error(request, "⛔ Solo el autor o el dueño del mundo pueden editar esta narrativa.")
             return redirect('leer_narrativa', nid=nid)
        # ----------------------

        if n_orm.world.status == 'LOCKED' and not request.user.is_superuser:
            messages.error(request, "⛔ El mundo está BLOQUEADO. No se pueden editar narrativas.")
            return redirect('leer_narrativa', nid=nid)
    else:
        return redirect('home')

    if request.method == 'POST':
        try:
            NarrativeService.handle_edit_proposal(
                user=request.user if request.user.is_authenticated else None,
                narrative_identifier=nid,
                title=request.POST.get('titulo'),
                content=request.POST.get('contenido'),
                reason=request.POST.get('change_reason', 'Edición estándar')
            )
            messages.success(request, "📝 Propuesta de cambio enviada para revisión.")
            return redirect('dashboard')

        except Exception as e: 
            print(f"Error: {e}")
            messages.error(request, f"Error al editar: {e}")
    return redirect('leer_narrativa', nid=nid)

@csrf_exempt
@login_required
@require_POST
def autosave_narrative(request, nid):
    """Guarda un borrador automático de la narrativa."""
    try:
        title = request.POST.get('titulo') or request.POST.get('title')
        content = request.POST.get('contenido') or request.POST.get('content')
        
        # Resolve narrative
        try: n_orm = CaosNarrativeORM.objects.get(nid=nid)
        except: n_orm = CaosNarrativeORM.objects.get(public_id=nid)

        # Check latest draft by this user
        draft, created = CaosNarrativeVersionORM.objects.get_or_create(
            narrative=n_orm,
            author=request.user,
            status='DRAFT',
            defaults={
                'proposed_title': title,
                'proposed_content': content,
                'version_number': n_orm.current_version_number + 1,
                'action': 'EDIT',
                'change_log': 'Auto-guardado'
            }
        )
        
        if not created:
            draft.proposed_title = title
            draft.proposed_content = content
            draft.save()
            
        return JsonResponse({'success': True, 'saved_at': draft.created_at.strftime('%H:%M:%S')})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def borrar_narrativa(request, nid):
    try:
        try: n = CaosNarrativeORM.objects.get(public_id=nid); real_nid = n.nid; w_pid = n.world.public_id
        except: n = CaosNarrativeORM.objects.get(nid=nid); real_nid = nid; w_pid = n.world.id
        
        # --- SECURITY CHECK ---
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        try:
            check_ownership(request.user, n)
        except:
             messages.error(request, "⛔ No puedes borrar lo que no es tuyo.")
             return redirect('leer_narrativa', nid=nid)
        # ----------------------

        # Create Deletion Proposal (Version)
        CaosNarrativeVersionORM.objects.create(
            narrative=n,
            proposed_title=f"BORRAR: {n.titulo}",
            proposed_content="Solicitud de borrado.",
            version_number=n.current_version_number + 1,
            status='PENDING',
            action='DELETE',
            change_log="Solicitud de eliminación",
            author=request.user if request.user.is_authenticated else None
        )
        
        messages.info(request, "🗑️ Solicitud de borrado enviada al Dashboard.")
        return redirect('ver_narrativa_mundo', jid=w_pid)
    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, f"Error al borrar: {e}")
        return redirect('home')

class NarrativeProxy:
    def __init__(self, nid, title, content, world, tipo, author, narrador="..."):
        self.nid = nid
        self.titulo = title
        self.contenido = content
        self.world = world
        self.tipo = tipo
        self.narrador = narrador
        self.created_by = author
        self.current_version_number = 0
        self.is_draft = True
        self.version_id = 0 # Dummy

def get_full_type(code):
    m = {'L':'LORE', 'H':'HISTORIA', 'C':'CAPITULO', 'E':'EVENTO', 'M':'LEYENDA', 'R':'REGLA', 'B':'BESTIARIO'}
    return m.get(code.upper(), 'LORE')

@login_required
def pre_crear_root(request, jid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        w_domain = resolve_world_id(repo, jid)
        w = CaosWorldORM.objects.get(id=w_domain.id.value)
        
        full_type = get_full_type(tipo_codigo)
        
        mock = NarrativeProxy(
            nid="NEW",
            title="Nuevo Documento",
            content="",
            world=w,
            tipo=full_type,
            author=request.user if request.user.is_authenticated else None
        )
        
        todas = CaosWorldORM.objects.all().order_by('id')
        
        return render(request, 'visor_narrativa.html', {
            'narr': mock,
            'todas_entidades': todas,
            'published_chapters': [],
            'is_creation_mode': True,
            'target_jid': jid,      # For Form Action
            'target_type': tipo_codigo, # For Form Action
            'current_period_slug': request.GET.get('period', 'actual')
        })
    except Exception as e:
        print(f"Error pre-creating root: {e}")
        return redirect('home')

@login_required
def pre_crear_child(request, parent_nid, tipo_codigo):
    try:
        try: p = CaosNarrativeORM.objects.get(public_id=parent_nid)
        except: p = CaosNarrativeORM.objects.get(nid=parent_nid)
        
        full_type = get_full_type(tipo_codigo)
        
        mock = NarrativeProxy(
            nid="NEW_CHILD",
            title="Nuevo Capítulo",
            content="",
            world=p.world,
            tipo=full_type,
            author=request.user if request.user.is_authenticated else None,
            narrador=p.narrador
        )
        
        todas = CaosWorldORM.objects.all().order_by('id')
        
        return render(request, 'visor_narrativa.html', {
            'narr': mock,
            'todas_entidades': todas,
            'published_chapters': [],
            'is_creation_mode': True,
            'is_child_mode': True,
            'target_parent': parent_nid, # For Form Action
            'target_type': tipo_codigo,
            'current_period_slug': request.GET.get('period', 'actual')
        })
    except Exception as e:
        print(f"Error pre-creating child: {e}")
        return redirect('home')

@login_required
def revisar_narrativa_version(request, version_id):
    try:
        v = CaosNarrativeVersionORM.objects.get(id=version_id)
        
        # Use global Proxy logic with Version data
        narr_proxy = NarrativeProxy(
            nid=v.narrative.nid,
            title=v.proposed_title,
            content=v.proposed_content,
            world=v.narrative.world,
            tipo=v.narrative.tipo,
            author=v.author,
            narrador=v.narrative.narrador
        )
        narr_proxy.version_id = v.id
        narr_proxy.is_proposal = True
        
        # Reuse the same template
        todas = CaosWorldORM.objects.all().order_by('id')
        hijos = CaosNarrativeORM.objects.filter(nid__startswith=narr_proxy.nid).exclude(nid=narr_proxy.nid).order_by('nid')
        published_chapters = hijos.filter(current_version_number__gt=0)
        
        messages.info(request, f"👁️ Visualizando PROPUESTA v{v.version_number}. Esto no es la versión live.")
        return render(request, 'visor_narrativa.html', {
            'narr': narr_proxy, 
            'todas_entidades': todas, 
            'published_chapters': published_chapters, 
            'is_proposal': True
        })
        
    except Exception as e:
        print(f"Error reviewing narrative version: {e}")
        messages.error(request, f"Error al revisar versión: {e}")
        return redirect('dashboard')

@login_required
def crear_nueva_narrativa(request, jid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        w = resolve_jid_orm(jid)
        if not w: return redirect('home')
        real_jid = w.id
        
        # --- SECURITY CHECK (Strict: Only World Owner can add roots) ---
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        try:
             # Need ORM object for check_ownership
             worm = CaosWorldORM.objects.get(id=real_jid)
             check_ownership(request.user, worm)
        except:
             messages.error(request, "⛔ Solo el dueño del mundo puede crear nuevas narrativas raíz.")
             return redirect('ver_mundo', public_id=jid)
        # ----------------------

        user = request.user if request.user.is_authenticated else None
        
        # Extract POST data
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        new_nid = CreateNarrativeUseCase(repo).execute(
            world_id=real_jid, 
            tipo_codigo=tipo_codigo, 
            user=user,
            title=title,
            content=content,
            period_slug=request.POST.get('period')
            # publish_immediately=False (Default) -> Crea V0 Pendiente
        )
        
        messages.success(request, "✨ Propuesta creada. Apruebala en el Dashboard para publicarla.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error creating narrative: {e}")
        return redirect('ver_mundo', public_id=jid)

@login_required
def crear_sub_narrativa(request, parent_nid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        repo = DjangoCaosRepository()
        try: p = CaosNarrativeORM.objects.get(public_id=parent_nid); real_parent = p.nid
        except: p = CaosNarrativeORM.objects.get(nid=parent_nid); real_parent = parent_nid
        
        # --- SECURITY CHECK (Ownership of Parent or World) ---
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        try:
             # If you own the parent narrative OR the world, you can add children?
             # Let's enforce strictness: You have to own the parent narrative (or be super)
             check_ownership(request.user, p)
        except:
             messages.error(request, "⛔ No puedes añadir capítulos a una narrativa ajena.")
             return redirect('leer_narrativa', nid=parent_nid)
        # ----------------------

        user = request.user if request.user.is_authenticated else None
        
        # Extract POST data
        title = request.POST.get('title')
        content = request.POST.get('content')

        new_nid = CreateNarrativeUseCase(repo).execute(
            world_id=None, 
            tipo_codigo=tipo_codigo, 
            parent_nid=real_parent, 
            user=user,
            title=title,
            content=content,
            period_slug=request.POST.get('period')
            # publish_immediately=False (Default) -> Crea V0 Pendiente
        )
        
        messages.success(request, "✨ Propuesta creada. Apruebala en el Dashboard para publicarla.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error creating sub-narrative: {e}")
        return redirect('leer_narrativa', nid=parent_nid)
