import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosNarrativeORM, CaosEventLog
from src.Shared.Domain import eclai_core
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.generate_creature_usecase import GenerateCreatureUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs, get_world_images


def log_event(user, action, target_id, details=""):
    try:
        u = user if user.is_authenticated else None
        CaosEventLog.objects.create(user=u, action=action, target_id=target_id, details=details)
    except Exception as e: print(f"Log Error: {e}")

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
        'visible': w.visible_publico, 'is_locked': w.is_locked, 'code_entity': eclai_core.encode_eclai126(jid),
        'nid_lore': w.id_lore, 'metadata': meta_str, 
        'metadata_obj': w.metadata, 'imagenes': imgs, 'hijos': hijos, 
        'breadcrumbs': generate_breadcrumbs(jid), 'propuestas': props, 'historial': historial
    }
    return render(request, 'ficha_mundo.html', context)

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

def toggle_visibilidad(request, jid):
    try: w=resolve_jid(jid); w.visible_publico=not w.visible_publico; w.save(); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')

def restaurar_version(request, version_id):
    try:
        v = CaosVersionORM.objects.get(id=version_id)
        RestoreVersionUseCase().execute(version_id, get_current_user(request))
        messages.success(request, "✅ Restaurada.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except: return redirect('home')

def comparar_version(request, version_id):
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

def escanear_planeta(request, jid): return redirect('ver_mundo', public_id=jid)

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

def toggle_lock(request, jid):
    """
    Función para bloquear/desbloquear un mundo (Solo Superadmin).
    """
    # 1. Seguridad: Si no eres el jefe, te echa
    if not request.user.is_superuser:
        return redirect('ver_mundo', public_id=jid)

    # 2. Buscar el mundo
    w = resolve_jid(jid)
    if not w:
        return redirect('home')

    # 3. Cambiar el estado
    if w.status == 'LOCKED':
        w.status = 'DRAFT' # Desbloqueamos a DRAFT por defecto
        messages.success(request, "🔓 Mundo desbloqueado.")
    else:
        w.status = 'LOCKED'
        messages.warning(request, "🔒 Mundo BLOQUEADO.")
    
    w.save()

    # 4. Volver a la ficha
    pid = w.public_id if w.public_id else w.id
    return redirect('ver_mundo', public_id=pid)