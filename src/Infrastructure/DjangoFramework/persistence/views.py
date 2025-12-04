import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosNarrativeORM, CaosEventLog

def log_event(user, action, target_id, details=""):
    try:
        u = user if user.is_authenticated else None
        CaosEventLog.objects.create(user=u, action=action, target_id=target_id, details=details)
    except Exception as e: print(f"Log Error: {e}")

# ... (Previous imports) ...

# ... (Inside views) ...

@csrf_exempt
def api_save_foto(request, jid):
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        data = json.loads(request.body)
        user = request.user.username if request.user.is_authenticated else "Anónimo"
        DjangoCaosRepository().save_image(real_jid, data.get('image'), title=data.get('title'), username=user)
        log_event(request.user, "UPLOAD_AI_PHOTO", real_jid, f"Title: {data.get('title')}")
        return JsonResponse({'status': 'ok', 'success': True})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

def subir_imagen_manual(request, jid):
    w = resolve_jid(jid)
    real_jid = w.id if w else jid
    redirect_target = jid 

    if request.method == 'POST' and request.FILES.get('imagen_manual'):
        try:
            repo = DjangoCaosRepository()
            use_orig = request.POST.get('use_original_name') == 'true' or request.POST.get('use_original_name') == 'on'
            custom = request.POST.get('custom_name')
            title = request.POST.get('manual_title', 'Sin Título')
            
            final = title
            if use_orig: final = request.FILES['imagen_manual'].name.split('.')[0]
            elif custom: final = custom

            user = request.user.username if request.user.is_authenticated else "Anónimo"
            repo.save_manual_file(real_jid, request.FILES['imagen_manual'], username=user, title=final)
            log_event(request.user, "UPLOAD_MANUAL_PHOTO", real_jid, f"File: {final}")
            messages.success(request, "✅ Imagen subida.")
        except Exception as e: messages.error(request, f"Error: {e}")
    return redirect('ver_mundo', public_id=redirect_target)

def editar_mundo(request, jid):
    if request.method == 'POST':
        try:
            w = resolve_jid(jid); real_jid = w.id if w else jid
            desc = request.POST.get('description')
            if request.POST.get('use_ai_edit') == 'on':
                try: desc = Llama3Service().generate_description(f"Nombre: {request.POST.get('name')}. Concepto: {desc}") or desc
                except: pass
            ProposeChangeUseCase().execute(real_jid, request.POST.get('name'), desc, request.POST.get('reason'), get_current_user(request))
            log_event(request.user, "PROPOSE_CHANGE", real_jid, f"Reason: {request.POST.get('reason')}")
            return redirect('ver_mundo', public_id=w.public_id if w.public_id else w.id)
        except: return redirect('home')
    return redirect('home')

def centro_control(request):
    pendientes = CaosVersionORM.objects.filter(status='PENDING').order_by('-created_at')
    aprobados = CaosVersionORM.objects.filter(status='APPROVED').order_by('-created_at')
    rechazados = CaosVersionORM.objects.filter(status='REJECTED').order_by('-created_at')[:10]
    archivados = CaosVersionORM.objects.filter(status='ARCHIVED').order_by('-created_at')[:10]
    logs = CaosEventLog.objects.all()[:20] # Last 20 events
    
    def map_v(v):
        return {
            'id': v.id,
            'version_num': v.version_number,
            'proposed_name': v.proposed_name,
            'author': v.author.username if v.author else 'Sistema',
            'reason': v.change_log,
            'date': v.created_at,
            'nivel_label': 'Mundo'
        }

    context = {
        'pendientes': [map_v(v) for v in pendientes],
        'aprobados': [map_v(v) for v in aprobados],
        'rechazados': [map_v(v) for v in rechazados],
        'archivados': [map_v(v) for v in archivados],
        'logs': logs
    }
    return render(request, 'control_panel.html', context)
from src.Shared.Domain import eclai_core
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
# Casos de uso
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.publish_world import PublishWorldUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.approve_version import ApproveVersionUseCase
from src.WorldManagement.Caos.Application.reject_version import RejectVersionUseCase
from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase
from src.WorldManagement.Caos.Application.generate_creature_usecase import GenerateCreatureUseCase
from src.WorldManagement.Caos.Application.update_narrative import UpdateNarrativeUseCase
from src.WorldManagement.Caos.Application.delete_narrative import DeleteNarrativeUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.create_narrative import CreateNarrativeUseCase
from src.WorldManagement.Caos.Application.generate_planet_metadata import GeneratePlanetMetadataUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
# Servicios
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs, get_world_images

def get_current_user(request):
    if request.user.is_authenticated: return request.user
    u, _ = User.objects.get_or_create(username='Admin')
    return u

def resolve_jid(identifier):
    """
    RESOLUCIÓN ROBUSTA DE IDs:
    No adivinamos por el formato. Probamos ambas llaves.
    """
    # 1. Intentar como Public ID (NanoID) - Prioridad Alta (URLs externas)
    try:
        return CaosWorldORM.objects.get(public_id=identifier)
    except CaosWorldORM.DoesNotExist:
        pass 

    # 2. Intentar como J-ID (Interno) - Prioridad Baja (URLs internas/admin)
    try:
        return CaosWorldORM.objects.get(id=identifier)
    except CaosWorldORM.DoesNotExist:
        return None

# ==============================================================================
#                                    CORE
# ==============================================================================

def home(request):
    if request.method == 'POST':
        repo = DjangoCaosRepository()
        jid = CreateWorldUseCase(repo).execute(request.POST.get('world_name'), request.POST.get('world_desc'))
        try: w = CaosWorldORM.objects.get(id=jid); return redirect('ver_mundo', public_id=w.public_id)
        except: return redirect('ver_mundo', public_id=jid)
    
    ms = CaosWorldORM.objects.filter(id__regex=r'^..$').order_by('id')
    l = []
    for m in ms:
        imgs = get_world_images(m.id)
        cover = imgs[0]['url'] if imgs else None
        if m.metadata and 'cover_image' in m.metadata:
            target = m.metadata['cover_image']
            found = next((i for i in imgs if i['filename'] == target), None)
            if found: cover = found['url']
        
        pid = m.public_id if m.public_id else m.id
        l.append({'id': m.id, 'public_id': pid, 'name': m.name, 'status': m.status, 'code': eclai_core.encode_eclai126(m.id), 'img_file': cover, 'has_img': bool(cover)})
    return render(request, 'index.html', {'mundos': l})

def ver_mundo(request, public_id):
    repo = DjangoCaosRepository()
    w = resolve_jid(public_id)
    if not w: 
        # Fallback de emergencia: si falla resolve, intentamos ID directo como string
        try: w = CaosWorldORM.objects.get(id=public_id)
        except: return render(request, '404.html', {"jid": public_id})
    
    jid = w.id
    safe_pid = w.public_id if w.public_id else jid

    if request.method == 'POST':
        if 'edit_mode' in request.POST: return editar_mundo(request, jid)
        child_name = request.POST.get('child_name')
        if child_name:
            if request.POST.get('child_type') == 'ENTITY' and request.POST.get('use_ai') == 'on':
                try: GenerateCreatureUseCase(repo, Llama3Service(), StableDiffusionService()).execute(jid)
                except: pass
            else:
                nid = CreateChildWorldUseCase(repo).execute(jid, child_name, request.POST.get('child_desc'))
                if request.POST.get('use_ai') == 'on':
                    try: GenerateWorldLoreUseCase(repo, Llama3Service()).execute(nid)
                    except: pass
                    try: GenerateWorldMapUseCase(repo, StableDiffusionService()).execute_single(nid)
                    except: pass
            return redirect('ver_mundo', public_id=safe_pid)

    props = w.versiones.filter(status='PENDING').order_by('-created_at')
    historial = w.versiones.exclude(status='PENDING').order_by('-version_number')[:10]
    
    len_h = len(jid)+2 if len(jid)<32 else len(jid)+4
    raw_hijos = CaosWorldORM.objects.filter(id__startswith=jid, id__regex=r'^.{'+str(len_h)+r'}$').order_by('id')
    hijos = []
    for h in raw_hijos:
        h_pid = h.public_id if h.public_id else h.id
        # Usamos J-ID para navegación interna
        hijos.append({'id': h.id, 'public_id': h.id, 'name': h.name, 'short': h.id[len(jid):], 'img':(get_world_images(h.id)[0]['url'] if get_world_images(h.id) else None)})
    
    imgs = get_world_images(jid)
    meta_str = json.dumps(w.metadata, indent=2) if w.metadata else "{}"
    last_live = w.versiones.filter(status='LIVE').order_by('-created_at').first()
    date_live = last_live.created_at if last_live else w.created_at

    context = {
        'name': w.name, 'description': w.description, 'jid': jid, 'public_id': safe_pid,
        'status': w.status, 'version_live': w.current_version_number,
        'author_live': getattr(w, 'current_author_name', 'Sistema'),
        'created_at': w.created_at, 'updated_at': date_live,
        'visible': w.visible_publico, 'code_entity': eclai_core.encode_eclai126(jid),
        'nid_lore': w.id_lore, 'metadata': meta_str, 
        'metadata_obj': w.metadata, 'imagenes': imgs, 'hijos': hijos, 
        'breadcrumbs': generate_breadcrumbs(jid), 'propuestas': props, 'historial': historial
    }
    return render(request, 'ficha_mundo.html', context)

# --- APIs ---
@csrf_exempt
def api_preview_foto(request, jid):
    if request.method != 'GET': return JsonResponse({'success': False})
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        b64 = GenerateWorldMapUseCase(DjangoCaosRepository(), StableDiffusionService()).generate_preview(real_jid)
        return JsonResponse({'status': 'ok', 'success': True, 'image': b64})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def api_save_foto(request, jid):
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        data = json.loads(request.body)
        user = request.user.username if request.user.is_authenticated else "Anónimo"
        DjangoCaosRepository().save_image(real_jid, data.get('image'), title=data.get('title'), username=user)
        log_event(request.user, "UPLOAD_AI_PHOTO", real_jid, f"Title: {data.get('title')}")
        return JsonResponse({'status': 'ok', 'success': True})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def api_update_image_metadata(request, jid):
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        data = json.loads(request.body)
        repo = DjangoCaosRepository()
        if hasattr(repo, 'update_image_metadata'):
            repo.update_image_metadata(real_jid, data.get('filename'), data.get('title'))
            return JsonResponse({'status': 'ok', 'success': True})
        return JsonResponse({'status': 'error', 'message': 'Repo method missing'})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

def subir_imagen_manual(request, jid):
    w = resolve_jid(jid)
    real_jid = w.id if w else jid
    redirect_target = jid 

    if request.method == 'POST' and request.FILES.get('imagen_manual'):
        try:
            repo = DjangoCaosRepository()
            use_orig = request.POST.get('use_original_name') == 'true' or request.POST.get('use_original_name') == 'on'
            custom = request.POST.get('custom_name')
            title = request.POST.get('manual_title', 'Sin Título')
            
            final = title
            if use_orig: final = request.FILES['imagen_manual'].name.split('.')[0]
            elif custom: final = custom

            user = request.user.username if request.user.is_authenticated else "Anónimo"
            repo.save_manual_file(real_jid, request.FILES['imagen_manual'], username=user, title=final)
            log_event(request.user, "UPLOAD_MANUAL_PHOTO", real_jid, f"File: {final}")
            messages.success(request, "✅ Imagen subida.")
        except Exception as e: messages.error(request, f"Error: {e}")
    return redirect('ver_mundo', public_id=redirect_target)

# --- RESTO DE VISTAS ---
def ver_narrativa_mundo(request, jid):
    try: 
        w = resolve_jid(jid)
        if not w: return redirect('home')
        
        docs = w.narrativas.exclude(tipo='CAPITULO')
        context = {'world': w, 'lores': docs.filter(tipo='LORE'), 'historias': docs.filter(tipo='HISTORIA'), 'eventos': docs.filter(tipo='EVENTO'), 'leyendas': docs.filter(tipo='LEYENDA'), 'reglas': docs.filter(tipo='REGLA'), 'bestiario': docs.filter(tipo='BESTIARIO')}
        return render(request, 'indice_narrativa.html', context)
    except: return redirect('home')

def leer_narrativa(request, nid):
    try:
        if len(nid) <= 12 and ('-' in nid or '_' in nid):
             narr = CaosNarrativeORM.objects.get(public_id=nid)
        else:
             narr = CaosNarrativeORM.objects.get(nid=nid)
    except: return redirect('home')
    
    todas = CaosWorldORM.objects.all().order_by('id')
    hijos = CaosNarrativeORM.objects.filter(nid__startswith=narr.nid).exclude(nid=narr.nid).order_by('nid')
    return render(request, 'visor_narrativa.html', {'narr': narr, 'todas_entidades': todas, 'capitulos': hijos})

def editar_narrativa(request, nid):
    if request.method == 'POST':
        try:
            try: n_obj = CaosNarrativeORM.objects.get(public_id=nid)
            except: n_obj = CaosNarrativeORM.objects.get(nid=nid)
            
            UpdateNarrativeUseCase().execute(
                nid=n_obj.nid,
                titulo=request.POST.get('titulo'),
                contenido=request.POST.get('contenido'),
                narrador=request.POST.get('narrador'),
                tipo=request.POST.get('tipo'),
                menciones_ids=request.POST.getlist('menciones')
            )
            messages.success(request, "Narrativa guardada.")
            return redirect('leer_narrativa', nid=nid)
        except Exception as e: print(f"Error: {e}")
    return redirect('leer_narrativa', nid=nid)

def borrar_narrativa(request, nid):
    try:
        try: n = CaosNarrativeORM.objects.get(public_id=nid); real_nid = n.nid; w_pid = n.world.public_id
        except: n = CaosNarrativeORM.objects.get(nid=nid); real_nid = nid; w_pid = n.world.id
        
        DeleteNarrativeUseCase().execute(real_nid)
        return redirect('ver_narrativa_mundo', jid=w_pid)
    except: return redirect('home')

def crear_nueva_narrativa(request, jid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        w = resolve_jid(jid)
        real_jid = w.id if w else jid
        user = request.user if request.user.is_authenticated else None
        new_nid = CreateNarrativeUseCase(repo).execute(world_id=real_jid, tipo_codigo=tipo_codigo, user=user)
        try: new_n = CaosNarrativeORM.objects.get(nid=new_nid); redir_id = new_n.public_id if new_n.public_id else new_nid
        except: redir_id = new_nid
        return redirect('leer_narrativa', nid=redir_id)
    except: return redirect('ver_mundo', public_id=jid)

def crear_sub_narrativa(request, parent_nid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        try: p = CaosNarrativeORM.objects.get(public_id=parent_nid); real_parent = p.nid
        except: real_parent = parent_nid
        user = request.user if request.user.is_authenticated else None
        new_nid = CreateNarrativeUseCase(repo).execute(world_id=None, tipo_codigo=tipo_codigo, parent_nid=real_parent, user=user)
        try: new_n = CaosNarrativeORM.objects.get(nid=new_nid); redir_id = new_n.public_id if new_n.public_id else new_nid
        except: redir_id = new_nid
        return redirect('leer_narrativa', nid=redir_id)
    except: return redirect('leer_narrativa', nid=parent_nid)

def restaurar_version(request, version_id):
    try:
        v = CaosVersionORM.objects.get(id=version_id)
        RestoreVersionUseCase().execute(version_id, get_current_user(request))
        messages.success(request, "✅ Restaurada.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except: return redirect('home')

def toggle_visibilidad(request, jid):
    try: w=resolve_jid(jid); w.visible_publico=not w.visible_publico; w.save(); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')
def set_cover_image(request, jid, filename):
    try: w=resolve_jid(jid); w.metadata['cover_image']=filename; w.save(); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')
def borrar_foto(request, jid, filename):
    try: 
        w=resolve_jid(jid); base=os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', w.id)
        if os.path.exists(os.path.join(base, filename)): os.remove(os.path.join(base, filename))
        return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')
def editar_mundo(request, jid):
    if request.method == 'POST':
        try:
            w = resolve_jid(jid); real_jid = w.id if w else jid
            desc = request.POST.get('description')
            if request.POST.get('use_ai_edit') == 'on':
                try: desc = Llama3Service().generate_description(f"Nombre: {request.POST.get('name')}. Concepto: {desc}") or desc
                except: pass
            ProposeChangeUseCase().execute(real_jid, request.POST.get('name'), desc, request.POST.get('reason'), get_current_user(request))
            log_event(request.user, "PROPOSE_CHANGE", real_jid, f"Reason: {request.POST.get('reason')}")
            return redirect('ver_mundo', public_id=w.public_id if w.public_id else w.id)
        except: return redirect('home')
    return redirect('home')
def borrar_mundo(request, jid): 
    try: CaosWorldORM.objects.get(id=jid).delete(); return redirect('home')
    except: return redirect('home')
def centro_control(request):
    pendientes = CaosVersionORM.objects.filter(status='PENDING').order_by('-created_at')
    aprobados = CaosVersionORM.objects.filter(status='APPROVED').order_by('-created_at')
    rechazados = CaosVersionORM.objects.filter(status='REJECTED').order_by('-created_at')[:10]
    archivados = CaosVersionORM.objects.filter(status='ARCHIVED').order_by('-created_at')[:10]
    logs = CaosEventLog.objects.all()[:20] # Last 20 events
    
    def map_v(v):
        return {
            'id': v.id,
            'version_num': v.version_number,
            'proposed_name': v.proposed_name,
            'author': v.author.username if v.author else 'Sistema',
            'reason': v.change_log,
            'date': v.created_at,
            'nivel_label': 'Mundo'
        }

    context = {
        'pendientes': [map_v(v) for v in pendientes],
        'aprobados': [map_v(v) for v in aprobados],
        'rechazados': [map_v(v) for v in rechazados],
        'archivados': [map_v(v) for v in archivados],
        'logs': logs
    }
    return render(request, 'control_panel.html', context)
def revisar_version(request, version_id):
    try:
        v = CaosVersionORM.objects.get(id=version_id)
        w = v.world
        # Renderizamos la ficha pero con los datos de la versión
        jid = w.id
        safe_pid = w.public_id if w.public_id else jid
        
        imgs = get_world_images(jid)
        meta_str = json.dumps(w.metadata, indent=2) if w.metadata else "{}"
        
        context = {
            'name': v.proposed_name, # DATOS DE LA VERSIÓN
            'description': v.proposed_description, # DATOS DE LA VERSIÓN
            'jid': jid, 'public_id': safe_pid,
            'status': f"PREVIEW v{v.version_number} ({v.status})",
            'version_live': w.current_version_number,
            'author_live': v.author.username if v.author else "Desconocido",
            'created_at': v.created_at, 'updated_at': v.created_at,
            'visible': False, 'code_entity': eclai_core.encode_eclai126(jid),
            'nid_lore': w.id_lore, 'metadata': meta_str, 
            'metadata_obj': w.metadata, 'imagenes': imgs, 'hijos': [], 
            'breadcrumbs': generate_breadcrumbs(jid), 
            'is_preview': True, 
            'preview_version_id': v.id
        }
        messages.info(request, f"👀 Viendo PREVISUALIZACIÓN de versión {v.version_number}")
        return render(request, 'ficha_mundo.html', context)
    except Exception as e: 
        print(e)
        return redirect('home')
def init_hemisferios(request, jid):
    try: w=resolve_jid(jid); InitializeHemispheresUseCase(DjangoCaosRepository()).execute(w.id); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')
def generar_foto_extra(request, jid): return redirect('ver_mundo', public_id=jid)
def escanear_planeta(request, jid): return redirect('ver_mundo', public_id=jid)
def dashboard(request):
    propuestas = CaosVersionORM.objects.filter(status='PENDING').order_by('-created_at')
    return render(request, 'dashboard.html', {'propuestas': propuestas})

def aprobar_propuesta(request, version_id):
    try:
        # 1. Aprobar (Internal Approval) - PENDING -> APPROVED
        ApproveVersionUseCase().execute(version_id)
        
        v = CaosVersionORM.objects.get(id=version_id)
        messages.success(request, f"✅ Propuesta v{v.version_number} de '{v.proposed_name}' APROBADA (Lista para Live).")
        return redirect('centro_control')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('centro_control')

def rechazar_propuesta(request, version_id):
    try:
        RejectVersionUseCase().execute(version_id)
        messages.warning(request, "❌ Propuesta rechazada.")
        return redirect('centro_control')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('centro_control')

def publicar_version(request, version_id):
    try:
        PublishToLiveVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        messages.success(request, f"🚀 Versión {v.version_number} PUBLICADA LIVE.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home')

def aprobar_version(request, version_id):
    try:
        ApproveVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        messages.success(request, f"✅ Versión {v.version_number} aprobada.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home')

def rechazar_version(request, version_id):
    try:
        RejectVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        messages.warning(request, f"❌ Versión {v.version_number} rechazada.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home')
def mapa_arbol(request, public_id):
    try:
        root = resolve_jid(public_id)
        if not root: return redirect('home')
        nodes = CaosWorldORM.objects.filter(id__startswith=root.id).order_by('id')
        tree_data = []
        base_len = len(root.id)
        for node in nodes:
            depth = (len(node.id) - base_len) // 2
            pid = node.public_id if node.public_id else node.id
            tree_data.append({'name': node.name, 'public_id': pid, 'id_display': node.id, 'indent_px': depth * 30, 'is_root': node.id == root.id, 'status': node.status})
        return render(request, 'mapa_arbol.html', {'root_name': root.name, 'tree': tree_data})
    except: return redirect('ver_mundo', public_id=public_id)
