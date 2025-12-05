from django.shortcuts import render, redirect
from django.contrib import messages
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosNarrativeORM, CaosNarrativeVersionORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.update_narrative import UpdateNarrativeUseCase
from src.WorldManagement.Caos.Application.delete_narrative import DeleteNarrativeUseCase
from src.WorldManagement.Caos.Application.create_narrative import CreateNarrativeUseCase
from src.WorldManagement.Caos.Application.propose_narrative_change import ProposeNarrativeChangeUseCase
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Application.get_narrative_details import GetNarrativeDetailsUseCase
from src.WorldManagement.Caos.Application.get_world_narratives import GetWorldNarrativesUseCase

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
            
            # Si hay una razón de cambio, es una PROPUESTA
            change_reason = request.POST.get('change_reason')
            
            if change_reason:
                ProposeNarrativeChangeUseCase().execute(
                    narrative_id=n_obj.nid,
                    new_title=request.POST.get('titulo'),
                    new_content=request.POST.get('contenido'),
                    reason=change_reason,
                    user=request.user if request.user.is_authenticated else None
                )
                messages.success(request, "📝 Propuesta de cambio enviada para revisión.")
                return redirect('dashboard')
            else:
                # Edición directa (Legacy / Admin bypass si se quisiera)
                UpdateNarrativeUseCase().execute(
                    nid=n_obj.nid,
                    titulo=request.POST.get('titulo'),
                    contenido=request.POST.get('contenido'),
                    narrador=request.POST.get('narrador'),
                    tipo=request.POST.get('tipo'),
                    menciones_ids=request.POST.getlist('menciones')
                )
                messages.success(request, "Narrativa guardada directamente.")
                return redirect('leer_narrativa', nid=nid)

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

def revisar_narrativa_version(request, version_id):
    try:
        v = CaosNarrativeVersionORM.objects.get(id=version_id)
        
        # Create a proxy object to mimic CaosNarrativeORM but with proposed data
        class NarrativeProxy:
            def __init__(self, version):
                self.nid = version.narrative.nid
                self.titulo = version.proposed_title
                self.contenido = version.proposed_content
                self.world = version.narrative.world
                self.created_by = version.author
                self.tipo = version.narrative.tipo
                self.narrador = version.narrative.narrador
                self.is_proposal = True
                self.version_id = version.id
        
        narr_proxy = NarrativeProxy(v)
        
        # Reuse the same template
        todas = CaosWorldORM.objects.all().order_by('id')
        hijos = CaosNarrativeORM.objects.filter(nid__startswith=narr_proxy.nid).exclude(nid=narr_proxy.nid).order_by('nid')
        
        messages.info(request, f"👁️ Visualizando PROPUESTA v{v.version_number}. Esto no es la versión live.")
        return render(request, 'visor_narrativa.html', {'narr': narr_proxy, 'todas_entidades': todas, 'capitulos': hijos, 'is_proposal': True})
        
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
            content=content
        )
        
        messages.success(request, "✨ Narrativa creada. Editando borrador...")
        # Redirect to read view with edit mode enabled
        try: n = CaosNarrativeORM.objects.get(nid=new_nid); redir_id = n.public_id if n.public_id else new_nid
        except: redir_id = new_nid
        return redirect(f"/narrativa/{redir_id}/?edit=true")
    except Exception as e: 
        print(f"Error creating narrative: {e}")
        return redirect('ver_mundo', public_id=jid)

def crear_sub_narrativa(request, parent_nid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        try: p = CaosNarrativeORM.objects.get(public_id=parent_nid); real_parent = p.nid
        except: real_parent = parent_nid
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
            content=content
        )
        
        messages.success(request, "✨ Sub-capítulo creado. Editando borrador...")
        try: new_n = CaosNarrativeORM.objects.get(nid=new_nid); redir_id = new_n.public_id if new_n.public_id else new_nid
        except: redir_id = new_nid
        return redirect(f"/narrativa/{redir_id}/?edit=true")
    except Exception as e: 
        print(f"Error creating sub-narrative: {e}")
        return redirect('leer_narrativa', nid=parent_nid)
