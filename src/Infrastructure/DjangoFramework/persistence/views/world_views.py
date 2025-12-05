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
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Application.toggle_visibility import ToggleWorldVisibilityUseCase
from src.WorldManagement.Caos.Application.toggle_lock import ToggleWorldLockUseCase
from src.WorldManagement.Caos.Application.get_world_tree import GetWorldTreeUseCase
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
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
    Delegamos en la utilidad compartida de Application Layer.
    """
    repo = DjangoCaosRepository()
    w = resolve_world_id(repo, identifier)
    if w:
        # Return ORM object for compatibility with existing views that expect it
        try: return CaosWorldORM.objects.get(id=w.id.value)
        except: return None
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
    
    # 1. Handle POST (Creation)
    if request.method == 'POST':
        # Resolve ID for parent (needed for creation)
        w = resolve_jid(public_id)
        if not w: return redirect('home') # Should handle better
        jid = w.id
        safe_pid = w.public_id if w.public_id else jid

        c_name = request.POST.get('child_name')
        if c_name:
            c_desc = request.POST.get('child_desc', "")
            reason = request.POST.get('reason', "Creación vía Wizard")
            use_ai = request.POST.get('use_ai_gen') == 'on'
            
            uc = CreateChildWorldUseCase(repo)
            new_id = uc.execute(parent_id=jid, name=c_name, description=c_desc, reason=reason, generate_image=use_ai)
            
            try:
                new_w = CaosWorldORM.objects.get(id=new_id)
                return redirect('ver_mundo', public_id=new_w.public_id if new_w.public_id else new_id)
            except:
                return redirect('ver_mundo', public_id=safe_pid)

    # 2. Handle GET (Display) via Use Case
    context = GetWorldDetailsUseCase(repo).execute(public_id, request.user)
    
    if not context:
        return render(request, '404.html', {"jid": public_id})

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
    try: 
        w = CaosWorldORM.objects.get(id=jid)
        parent_id = jid[:-2]
        
        # Determine redirect target BEFORE deletion
        redirect_target = 'home'
        if len(parent_id) >= 2:
            try:
                p = CaosWorldORM.objects.get(id=parent_id)
                redirect_target = p.public_id if p.public_id else p.id
            except: pass
            
        w.delete()
        
        if redirect_target == 'home': return redirect('home')
        return redirect('ver_mundo', public_id=redirect_target)
    except: return redirect('home')

def toggle_visibilidad(request, jid):
    try: 
        repo = DjangoCaosRepository()
        ToggleWorldVisibilityUseCase(repo).execute(jid)
        # Redirect logic needs to find the public_id again or use the one returned
        w = resolve_world_id(repo, jid)
        w_orm = CaosWorldORM.objects.get(id=w.id.value)
        return redirect('ver_mundo', public_id=w_orm.public_id if w_orm.public_id else w_orm.id)
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
        repo = DjangoCaosRepository()
        result = GetWorldTreeUseCase(repo).execute(public_id)
        if not result: return redirect('home')
        return render(request, 'mapa_arbol.html', result)
    except: return redirect('ver_mundo', public_id=public_id)

def toggle_lock(request, jid):
    if not request.user.is_superuser:
        return redirect('ver_mundo', public_id=jid)
    
    try:
        repo = DjangoCaosRepository()
        ToggleWorldLockUseCase(repo).execute(jid)
        w = resolve_world_id(repo, jid)
        w_orm = CaosWorldORM.objects.get(id=w.id.value)
        if w_orm.is_locked: messages.warning(request, "🔒 Mundo BLOQUEADO.")
        else: messages.success(request, "🔓 Mundo desbloqueado.")
        return redirect('ver_mundo', public_id=w_orm.public_id if w_orm.public_id else w_orm.id)
    except: return redirect('home')