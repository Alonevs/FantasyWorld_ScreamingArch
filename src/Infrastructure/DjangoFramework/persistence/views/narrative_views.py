from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosNarrativeORM, CaosNarrativeVersionORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.update_narrative import UpdateNarrativeUseCase
from src.WorldManagement.Caos.Application.delete_narrative import DeleteNarrativeUseCase
from src.WorldManagement.Caos.Application.create_narrative import CreateNarrativeUseCase
from src.WorldManagement.Caos.Application.propose_narrative_change import ProposeNarrativeChangeUseCase
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Application.get_narrative_details import GetNarrativeDetailsUseCase
from src.WorldManagement.Caos.Application.get_world_narratives import GetWorldNarrativesUseCase
from src.Infrastructure.Utils.FileExtractor import FileExtractor

@csrf_exempt
@require_POST
def import_narrative_file(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo.'}, status=400)
        
        uploaded_file = request.FILES['file']
        text = FileExtractor.extract_text_from_file(uploaded_file)
        
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

def ver_narrativa_mundo(request, jid):
    try: 
        repo = DjangoCaosRepository()
        context = GetWorldNarrativesUseCase(repo).execute(jid, request.user)
        
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
        context = GetNarrativeDetailsUseCase(repo).execute(nid, request.user)
        
        if not context:
            messages.error(request, f"No se encontró la narrativa: {nid}")
            return redirect('home')

        return render(request, 'visor_narrativa.html', context)
    except Exception as e:
        print(f"❌ Error al leer narrativa '{nid}': {e}")
        messages.error(request, f"Error interno al leer narrativa: {nid}")
        return redirect('home')

def editar_narrativa(request, nid):
    if request.method == 'POST':
        try:
            try: n_obj = CaosNarrativeORM.objects.get(public_id=nid)
            except: n_obj = CaosNarrativeORM.objects.get(nid=nid)
            
            # ENFORCE PROPOSAL FOR ALL EDITS
            change_reason = request.POST.get('change_reason', 'Edición estándar')
            
            ProposeNarrativeChangeUseCase().execute(
                narrative_id=n_obj.nid,
                new_title=request.POST.get('titulo'),
                new_content=request.POST.get('contenido'),
                reason=change_reason,
                user=request.user if request.user.is_authenticated else None
            )
            messages.success(request, "📝 Propuesta de cambio enviada para revisión.")
            return redirect('dashboard')

        except Exception as e: 
            print(f"Error: {e}")
            messages.error(request, f"Error al editar: {e}")
    return redirect('leer_narrativa', nid=nid)

def borrar_narrativa(request, nid):
    try:
        try: n = CaosNarrativeORM.objects.get(public_id=nid); real_nid = n.nid; w_pid = n.world.public_id
        except: n = CaosNarrativeORM.objects.get(nid=nid); real_nid = nid; w_pid = n.world.id
        
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

def crear_nueva_narrativa(request, jid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        w = resolve_jid(jid)
        real_jid = w.id if w else jid
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

def crear_sub_narrativa(request, parent_nid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        try: p = CaosNarrativeORM.objects.get(public_id=parent_nid); real_parent = p.nid
        except: p = CaosNarrativeORM.objects.get(nid=parent_nid); real_parent = parent_nid
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
