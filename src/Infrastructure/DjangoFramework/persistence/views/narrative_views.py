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

def resolve_jid(identifier):
    repo = DjangoCaosRepository()
    w = resolve_world_id(repo, identifier)
    if w:
        try: return CaosWorldORM.objects.get(id=w.id.value)
        except: return None
    return None

from django.http import Http404

def ver_narrativa_mundo(request, jid):
    try: 
        repo = DjangoCaosRepository()
        
        # Visibility Check
        w = resolve_jid(jid)
        if w:
            is_live = (w.status == 'LIVE')
            is_author = (request.user.is_authenticated and w.author == request.user)
            is_superuser = request.user.is_superuser
        if not (is_live or is_author or is_superuser): 
                return render(request, 'private_access.html', status=403)
            
        real_jid = w.id if w else jid
        context = GetWorldNarrativesUseCase(repo).execute(real_jid, request.user)
        
        if not context: 
            print(f"❌ Mundo no encontrado para JID: {jid}")
            messages.error(request, f"Mundo no encontrado: {jid}")
            return redirect('home')
        
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
           w = n_orm.world
           is_live = (w.status == 'LIVE')
           is_strict_author = (request.user.is_authenticated and w.author == request.user)
           is_superuser = request.user.is_superuser
           
           # Check Collaborator Status
           is_collaborator = False
           if request.user.is_authenticated and not is_strict_author:
               try:
                    if w.author and hasattr(w.author, 'profile'):
                        if request.user.profile in w.author.profile.collaborators.all():
                            is_collaborator = True
               except: pass

           check_access = is_live or is_strict_author or is_superuser or is_collaborator
           if not check_access: 
               return render(request, 'private_access.html', status=403)

        context = GetNarrativeDetailsUseCase(repo).execute(nid, request.user)
        
        # Patch Context with Permissions
        if context:
           # Check Admin Role
           is_admin_role = False
           try: is_admin_role = (request.user.profile.rank == 'ADMIN')
           except: pass
           
           context['is_author'] = is_strict_author or is_collaborator or is_admin_role
           context['allow_proposals'] = is_collaborator or is_admin_role
           context['is_admin_role'] = is_admin_role
        
        if not context:
            messages.error(request, f"No se encontró la narrativa: {nid}")
            return redirect('home')

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
            'target_type': tipo_codigo # For Form Action
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
            'target_type': tipo_codigo
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
        repo = DjangoCaosRepository()
        w = resolve_jid(jid)
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
            # publish_immediately=False (Default) -> Crea V0 Pendiente
        )
        
        messages.success(request, "✨ Propuesta creada. Apruebala en el Dashboard para publicarla.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error creating sub-narrative: {e}")
        return redirect('leer_narrativa', nid=parent_nid)
