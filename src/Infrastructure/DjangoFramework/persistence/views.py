import os
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from src.Shared.Domain import eclai_core

# --- IMPORTS DE CASOS DE USO ---
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.publish_world import PublishWorldUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.approve_version import ApproveVersionUseCase
from src.WorldManagement.Caos.Application.reject_version import RejectVersionUseCase
from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService

# --- HELPERS ---
def get_current_user(request):
    if request.user.is_authenticated: return request.user
    u, _ = User.objects.get_or_create(username='Admin')
    return u

def get_world_images(jid):
    base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
    target = os.path.join(base, jid)
    if not os.path.exists(target):
        for d in os.listdir(base):
            if d.startswith(f"{jid}_"): target = os.path.join(base, d); break
    imgs = []
    if os.path.exists(target):
        dname = os.path.basename(target)
        for f in sorted(os.listdir(target)):
            if f.endswith('.png'): imgs.append(f'{dname}/{f}')
    return imgs

# --- VISTAS DE GESTIÓN ---

def borrar_mundo(request, jid):
    try:
        mundo = CaosWorldORM.objects.get(id=jid)
        padre_id = jid[:-2] if len(jid) > 2 else None
        mundo.delete()
        return redirect('ver_mundo', jid=padre_id) if padre_id else redirect('home')
    except: return redirect('home')

def editar_mundo(request, jid):
    if request.method == 'POST':
        ProposeChangeUseCase().execute(
            jid, 
            request.POST.get('name'), 
            request.POST.get('description'), 
            request.POST.get('reason'), 
            get_current_user(request)
        )
        return redirect('ver_mundo', jid=jid)
    return redirect('ver_mundo', jid=jid)

def aprobar_version(request, version_id):
    try: 
        ApproveVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        return redirect('ver_mundo', jid=v.world.id)
    except: return redirect('home')

def rechazar_version(request, version_id):
    try: 
        RejectVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        return redirect('ver_mundo', jid=v.world.id)
    except: return redirect('home')

def publicar_version(request, version_id):
    try: 
        PublishToLiveVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        return redirect('ver_mundo', jid=v.world.id)
    except: return redirect('centro_control')

def generar_foto_extra(request, jid):
    try: GenerateWorldMapUseCase(DjangoCaosRepository(), StableDiffusionService()).execute_single(jid)
    except: pass
    return redirect('ver_mundo', jid=jid)

# --- VISTAS PRINCIPALES ---

def centro_control(request):
    todas = CaosVersionORM.objects.all().order_by('-created_at')
    pendientes, aprobados, rechazados, archivados = [], [], [], []
    for v in todas:
        l = len(v.world.id)
        niv = 1 if l==2 else (2 if l==4 else l//2)
        d = {
            'id': v.id, 'world_name': v.world.name, 'world_id': v.world.id,
            'version_num': v.version_number, 'proposed_name': v.proposed_name,
            'reason': v.change_log, 'date': v.created_at, 
            'author': v.author.username if v.author else 'Desconocido',
            'nivel_label': f"NIVEL {niv}"
        }
        if v.status == 'PENDING': pendientes.append(d)
        elif v.status == 'APPROVED': aprobados.append(d)
        elif v.status == 'REJECTED': rechazados.append(d)
        elif v.status == 'ARCHIVED': archivados.append(d)
    return render(request, 'control_panel.html', {'pendientes': pendientes, 'aprobados': aprobados, 'rechazados': rechazados, 'archivados': archivados})

def revisar_version(request, version_id):
    # ESTA ES LA QUE FALTABA
    try:
        version = CaosVersionORM.objects.get(id=version_id)
        world = version.world
    except CaosVersionORM.DoesNotExist:
        return redirect('centro_control')

    # Simulamos datos
    imgs = get_world_images(world.id)
    bread = [{'id': world.id[0:i+2]} for i in range(0, len(world.id), 2)]
    
    # Hijos reales
    len_h = len(world.id)+2 if len(world.id)<32 else len(world.id)+4
    hijos = [{'id':h.id, 'name':h.name, 'code':eclai_core.encode_eclai126(h.id), 'img':(get_world_images(h.id)[0] if get_world_images(h.id) else None)} for h in CaosWorldORM.objects.filter(id__startswith=world.id, id__regex=r'^.{'+str(len_h)+r'}$')]

    context = {
        'name': version.proposed_name, # FALSO
        'description': version.proposed_description, # FALSO
        'jid': world.id,
        'status': f"PREVIEW v{version.version_number}",
        'code_entity': eclai_core.encode_eclai126(world.id),
        'nid_lore': eclai_core.generar_nid(world.id, "L", 1),
        'code_lore': eclai_core.encode_eclai126(eclai_core.generar_nid(world.id, "L", 1)),
        'imagenes': imgs, 'hijos': hijos, 'breadcrumbs': bread,
        'is_preview': True,
        'version_id': version.id,
        'change_log': version.change_log,
        'author': version.author.username if version.author else 'Desconocido'
    }
    return render(request, 'ficha_mundo.html', context)

def ver_mundo(request, jid):
    repo = DjangoCaosRepository()
    if request.method == 'POST':
        if 'edit_mode' in request.POST: return editar_mundo(request, jid)
        child_name = request.POST.get('child_name')
        if child_name:
            nid = CreateChildWorldUseCase(repo).execute(jid, child_name, request.POST.get('child_desc'))
            try: GenerateWorldLoreUseCase(repo, Llama3Service()).execute(nid)
            except: pass
            try: GenerateWorldMapUseCase(repo, StableDiffusionService()).execute(nid)
            except: pass
            PublishWorldUseCase(repo).execute(nid)
            return redirect('ver_mundo', jid=jid)

    try: w = CaosWorldORM.objects.get(id=jid)
    except: return render(request, '404.html', {"jid": jid})

    props = w.versiones.filter(status='PENDING').order_by('-created_at')
    len_h = len(jid)+2 if len(jid)<32 else len(jid)+4
    hijos = [{'id':h.id, 'name':h.name, 'code':eclai_core.encode_eclai126(h.id), 'img':(get_world_images(h.id)[0] if get_world_images(h.id) else None)} for h in CaosWorldORM.objects.filter(id__startswith=jid, id__regex=r'^.{'+str(len_h)+r'}$')]
    imgs = get_world_images(jid)
    bread = [{'id': jid[0:i+2]} for i in range(0, len(jid), 2)]

    context = {
        'name': w.name, 'description': w.description, 'jid': jid,
        'status': w.status, 'version_live': w.current_version_number,
        'code_entity': eclai_core.encode_eclai126(jid),
        'nid_lore': eclai_core.generar_nid(jid, "L", 1), 'code_lore': eclai_core.encode_eclai126(eclai_core.generar_nid(jid, "L", 1)),
        'imagenes': imgs, 'hijos': hijos, 'breadcrumbs': bread, 'propuestas': props
    }
    return render(request, 'ficha_mundo.html', context)

def home(request):
    if request.method == 'POST':
        repo = DjangoCaosRepository()
        jid = CreateWorldUseCase(repo).execute(request.POST.get('world_name'), request.POST.get('world_desc'))
        try: GenerateWorldLoreUseCase(repo, Llama3Service()).execute(jid)
        except: pass
        try: GenerateWorldMapUseCase(repo, StableDiffusionService()).execute(jid)
        except: pass
        PublishWorldUseCase(repo).execute(jid)
        return redirect('ver_mundo', jid=jid)

    ms = CaosWorldORM.objects.filter(id__regex=r'^..$').order_by('-created_at')
    l = [{'id': m.id, 'name': m.name, 'status': m.status, 'code': eclai_core.encode_eclai126(m.id), 'img_file': (get_world_images(m.id)[0] if get_world_images(m.id) else None), 'has_img': bool(get_world_images(m.id))} for m in ms]
    return render(request, 'index.html', {'mundos': l})