import os
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from src.Shared.Domain import eclai_core

# Imports de Aplicación
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.create_entity_full import CreateEntityFullUseCase
from src.WorldManagement.Caos.Application.publish_world import PublishWorldUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.approve_version import ApproveVersionUseCase
from src.WorldManagement.Caos.Application.reject_version import RejectVersionUseCase
from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService

def get_current_user(request):
    if request.user.is_authenticated: return request.user
    u, _ = User.objects.get_or_create(username='Admin')
    return u

def get_world_images(jid):
    # Busca imágenes en la carpeta del ID o por prefijo
    base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
    target = os.path.join(base, jid)
    if not os.path.exists(target):
        for d in os.listdir(base):
            if d.startswith(f"{jid}_"): target = os.path.join(base, d); break
    imgs = []
    if os.path.exists(target):
        dname = os.path.basename(target)
        for f in sorted(os.listdir(target)):
            if f.endswith('.png'): 
                # Devolvemos diccionario para facilitar el uso en template
                imgs.append({'url': f'{dname}/{f}', 'filename': f})
    return imgs

# --- ACCIONES MANUALES ---
def generar_foto_extra(request, jid):
    try: GenerateWorldMapUseCase(DjangoCaosRepository(), StableDiffusionService()).execute_single(jid)
    except: pass
    return redirect('ver_mundo', jid=jid)

def generar_texto_extra(request, jid):
    try: GenerateWorldLoreUseCase(DjangoCaosRepository(), Llama3Service()).execute(jid)
    except: pass
    return redirect('ver_mundo', jid=jid)

def borrar_foto(request, jid, filename):
    base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
    target_dir = os.path.join(base, jid)
    if not os.path.exists(target_dir):
        for d in os.listdir(base):
            if d.startswith(f"{jid}_"): target_dir = os.path.join(base, d); break
    
    file_path = os.path.join(target_dir, filename)
    if os.path.exists(file_path) and filename.endswith('.png'):
        try: os.remove(file_path)
        except: pass
    return redirect('ver_mundo', jid=jid)

def toggle_visibilidad(request, jid):
    try:
        w = CaosWorldORM.objects.get(id=jid)
        w.visible_publico = not w.visible_publico
        w.save()
    except: pass
    return redirect('ver_mundo', jid=jid)

# --- GESTIÓN ---
def editar_mundo(request, jid):
    if request.method == 'POST':
        desc = request.POST.get('description')
        if request.POST.get('use_ai_edit') == 'on':
            try:
                prompt = f"Nombre: {request.POST.get('name')}. Concepto: {desc}"
                generated = Llama3Service().generate_description(prompt)
                if generated: desc = generated
            except: pass

        ProposeChangeUseCase().execute(
            jid, request.POST.get('name'), desc, 
            request.POST.get('reason'), get_current_user(request)
        )
    return redirect('ver_mundo', jid=jid)

def aprobar_version(request, version_id):
    try: ApproveVersionUseCase().execute(version_id); return redirect('ver_mundo', jid=CaosVersionORM.objects.get(id=version_id).world.id)
    except: return redirect('home')

def rechazar_version(request, version_id):
    try: RejectVersionUseCase().execute(version_id); return redirect('ver_mundo', jid=CaosVersionORM.objects.get(id=version_id).world.id)
    except: return redirect('home')

def publicar_version(request, version_id):
    try: PublishToLiveVersionUseCase().execute(version_id); return redirect('ver_mundo', jid=CaosVersionORM.objects.get(id=version_id).world.id)
    except: return redirect('centro_control')

def borrar_mundo(request, jid):
    try: CaosWorldORM.objects.get(id=jid).delete(); return redirect('home')
    except: return redirect('home')

# --- VISTAS PRINCIPALES ---
def ver_mundo(request, jid):
    repo = DjangoCaosRepository()
    if request.method == 'POST':
        if 'edit_mode' in request.POST: return editar_mundo(request, jid)
        
        child_name = request.POST.get('child_name')
        child_type = request.POST.get('child_type')
        
        if child_name:
            if child_type == 'ENTITY':
                CreateEntityFullUseCase(repo).execute(jid, child_name, "Criatura")
            else:
                CreateChildWorldUseCase(repo).execute(jid, child_name, request.POST.get('child_desc'))
            return redirect('ver_mundo', jid=jid)

    try: w = CaosWorldORM.objects.get(id=jid)
    except: return render(request, '404.html', {"jid": jid})

    props = w.versiones.filter(status='PENDING').order_by('-created_at')
    historial = w.versiones.exclude(status='PENDING').order_by('-version_number')[:10]
    
    len_h = len(jid)+2 if len(jid)<32 else len(jid)+4
    hijos = [{'id':h.id, 'name':h.name, 'code':eclai_core.encode_eclai126(h.id), 'img':(get_world_images(h.id)[0]['url'] if get_world_images(h.id) else None), 'short': h.id[len(jid):]} for h in CaosWorldORM.objects.filter(id__startswith=jid, id__regex=r'^.{'+str(len_h)+r'}$')]
    
    imgs = get_world_images(jid)
    
    bread = []
    for i in range(0, len(jid), 2):
        chunk = jid[0 : i+2]
        lvl = (i // 2) + 1
        bread.append({'id': chunk, 'label': f"Nivel {lvl}"})

    meta_str = json.dumps(w.metadata, indent=2) if w.metadata else "{}"
    last_live = w.versiones.filter(status='LIVE').order_by('-created_at').first()
    date_live = last_live.created_at if last_live else w.created_at

    context = {
        'name': w.name, 'description': w.description, 'jid': jid,
        'status': w.status, 
        'version_live': w.current_version_number,
        'author_live': getattr(w, 'current_author_name', 'Sistema'),
        'created_at': w.created_at, 'updated_at': date_live,
        'visible': w.visible_publico,
        'code_entity': eclai_core.encode_eclai126(jid),
        'nid_lore': f"{jid}L{eclai_core.encode_eclai126(jid)[:2]}",
        'metadata': meta_str, 'imagenes': imgs, 'hijos': hijos, 
        'breadcrumbs': bread, 'propuestas': props, 'historial': historial
    }
    return render(request, 'ficha_mundo.html', context)

def revisar_version(request, version_id):
    try: v = CaosVersionORM.objects.get(id=version_id); w = v.world
    except: return redirect('centro_control')
    imgs = get_world_images(w.id)
    bread = [{'id': w.id[0:i+2], 'label': f"Nivel {(i//2)+1}"} for i in range(0, len(w.id), 2)]
    context = {
        'name': v.proposed_name, 'description': v.proposed_description,
        'jid': w.id, 'status': f"PREVIEW v{v.version_number}",
        'code_entity': eclai_core.encode_eclai126(w.id), 
        'nid_lore': f"{w.id}L{eclai_core.encode_eclai126(w.id)[:2]}",
        'imagenes': imgs, 'hijos': [], 'breadcrumbs': bread,
        'is_preview': True, 'version_id': v.id, 'change_log': v.change_log, 'author': v.author.username if v.author else '?'
    }
    return render(request, 'ficha_mundo.html', context)

def centro_control(request):
    todas = CaosVersionORM.objects.all().order_by('-created_at')
    p, a, r, h = [], [], [], []
    for v in todas:
        l = len(v.world.id)
        niv = 1 if l==2 else (2 if l==4 else l//2)
        d = {'id': v.id, 'world_name': v.world.name, 'world_id': v.world.id, 'version_num': v.version_number, 'proposed_name': v.proposed_name, 'reason': v.change_log, 'date': v.created_at, 'author': v.author.username if v.author else '?', 'nivel_label': f"NIVEL {niv}"}
        if v.status == 'PENDING': p.append(d)
        elif v.status == 'APPROVED': a.append(d)
        elif v.status == 'REJECTED': r.append(d)
        elif v.status in ['ARCHIVED', 'LIVE']: h.append(d)
    return render(request, 'control_panel.html', {'pendientes': p, 'aprobados': a, 'rechazados': r, 'archivados': h})

def home(request):
    if request.method == 'POST':
        repo = DjangoCaosRepository()
        jid = CreateWorldUseCase(repo).execute(request.POST.get('world_name'), request.POST.get('world_desc'))
        
        if request.POST.get('use_ai') == 'on':
            try: GenerateWorldLoreUseCase(repo, Llama3Service()).execute(jid)
            except: pass
            
        # Generar foto inicial
        try: GenerateWorldMapUseCase(repo, StableDiffusionService()).execute_single(jid)
        except: pass

        return redirect('ver_mundo', jid=jid)

    ms = CaosWorldORM.objects.filter(id__regex=r'^..$').order_by('-created_at')
    l = []
    for m in ms:
        imgs = get_world_images(m.id)
        thumb = imgs[0]['url'] if imgs else None
        l.append({'id': m.id, 'name': m.name, 'status': m.status, 'code': eclai_core.encode_eclai126(m.id), 'img_file': thumb, 'has_img': thumb is not None})
    return render(request, 'index.html', {'mundos': l})