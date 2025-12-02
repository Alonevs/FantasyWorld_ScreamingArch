from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
import os
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosNarrativeORM
from src.Shared.Domain import eclai_core

# Use Cases
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
from src.WorldManagement.Caos.Application.generate_creature_usecase import GenerateCreatureUseCase
from src.WorldManagement.Caos.Application.update_narrative import UpdateNarrativeUseCase
from src.WorldManagement.Caos.Application.delete_narrative import DeleteNarrativeUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.create_narrative import CreateNarrativeUseCase

from src.WorldManagement.Caos.Application.create_narrative import CreateNarrativeUseCase
from src.WorldManagement.Caos.Application.generate_planet_metadata import GeneratePlanetMetadataUseCase

# Services
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service

from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs, get_world_images


def get_current_user(request):
    if request.user.is_authenticated: return request.user
    u, _ = User.objects.get_or_create(username='Admin')
    return u

# --- ACCIONES MANUALES ---
def generar_foto_extra(request, jid):
    try: 
        GenerateWorldMapUseCase(DjangoCaosRepository(), StableDiffusionService()).execute_single(jid)
    except Exception as e:
        print(f"Error generating extra photo: {e}")
    return redirect('ver_mundo', jid=jid)

# --- API JSON (AJAX) ---
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def api_preview_foto(request, jid):
    try:
        # Generamos la imagen pero NO la guardamos
        b64 = GenerateWorldMapUseCase(DjangoCaosRepository(), StableDiffusionService()).generate_preview(jid)
        if b64:
            return JsonResponse({'success': True, 'image': b64})
        return JsonResponse({'success': False, 'error': 'No image generated'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_save_foto(request, jid):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            img_b64 = data.get('image')
            title = data.get('title')
            
            username = request.user.username if request.user.is_authenticated else "Anonymous"
            
            repo = DjangoCaosRepository()
            repo.save_image(jid, img_b64, title=title, username=username)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

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
    if os.path.exists(file_path):
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

def escanear_planeta(request, jid):
    try:
        GeneratePlanetMetadataUseCase(DjangoCaosRepository(), Llama3Service()).execute(jid)
    except Exception as e:
        print(f"Error escaneando: {e}")
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

def borrar_mundo(request, jid):
    try: CaosWorldORM.objects.get(id=jid).delete(); return redirect('home')
    except: return redirect('home')

# --- NARRATIVA (BIBLIOTECA) ---
def ver_narrativa_mundo(request, jid):
    try:
        w = CaosWorldORM.objects.get(id=jid)
        docs = w.narrativas.exclude(tipo='CAPITULO')
        context = {
            'world': w,
            'lores': docs.filter(tipo='LORE'),
            'historias': docs.filter(tipo='HISTORIA'),
            'eventos': docs.filter(tipo='EVENTO'),
            'leyendas': docs.filter(tipo='LEYENDA'),
            'reglas': docs.filter(tipo='REGLA'),
            'bestiario': docs.filter(tipo='BESTIARIO'),
        }
        return render(request, 'indice_narrativa.html', context)
    except CaosWorldORM.DoesNotExist:
        return redirect('home')

def leer_narrativa(request, nid):
    try:
        narr = CaosNarrativeORM.objects.get(nid=nid)
        todas = CaosWorldORM.objects.all().order_by('id')
        hijos = CaosNarrativeORM.objects.filter(nid__startswith=narr.nid).exclude(nid=narr.nid).order_by('nid')
        return render(request, 'visor_narrativa.html', {'narr': narr, 'todas_entidades': todas, 'capitulos': hijos})
    except CaosNarrativeORM.DoesNotExist:
        return redirect('home')

def editar_narrativa(request, nid):
    if request.method == 'POST':
        try:
            UpdateNarrativeUseCase().execute(
                nid=nid,
                titulo=request.POST.get('titulo'),
                contenido=request.POST.get('contenido'),
                narrador=request.POST.get('narrador'),
                tipo=request.POST.get('tipo'),
                menciones_ids=request.POST.getlist('menciones')
            )
        except Exception as e:
            print(f"Error editando: {e}")
    return redirect('leer_narrativa', nid=nid)

def borrar_narrativa(request, nid):
    try:
        world_id = DeleteNarrativeUseCase().execute(nid)
        return redirect('ver_narrativa_mundo', jid=world_id)
    except: return redirect('home')

def crear_nueva_narrativa(request, jid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        
        user = request.user if request.user.is_authenticated else None
        new_nid = CreateNarrativeUseCase(repo).execute(world_id=jid, tipo_codigo=tipo_codigo, user=user)
        return redirect('editar_narrativa', nid=new_nid)
    except Exception as e:
        messages.error(request, f"Error creando narrativa: {e}")
        return redirect('ver_narrativa_mundo', jid=jid)

def crear_sub_narrativa(request, parent_nid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        
        user = request.user if request.user.is_authenticated else None
        new_nid = CreateNarrativeUseCase(repo).execute(world_id=None, tipo_codigo=tipo_codigo, parent_nid=parent_nid, user=user)
        return redirect('editar_narrativa', nid=new_nid)
    except Exception as e:
        messages.error(request, f"Error creando sub-narrativa: {e}")
        return redirect('leer_narrativa', nid=parent_nid)


def set_cover_image(request, jid, filename):
    try:
        w = CaosWorldORM.objects.get(id=jid)
        if not w.metadata: w.metadata = {}
        w.metadata['cover_image'] = filename
        w.save()
        messages.success(request, f"⭐ Portada actualizada: {filename}")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect('ver_mundo', jid=jid)

def subir_imagen_manual(request, jid):
    if request.method == 'POST' and request.FILES.get('imagen_manual'):
        try:
            repo = DjangoCaosRepository()
            if repo.save_manual_file(jid, request.FILES['imagen_manual'], request.user.username):
                messages.success(request, "✅ Imagen guardada correctamente.")
            else:
                messages.error(request, "❌ Error al guardar imagen.")
        except Exception as e:
            messages.error(request, f"Error crítico: {e}")
    return redirect('ver_mundo', jid=jid)

def init_hemisferios(request, jid):
    try:
        repo = DjangoCaosRepository()
        InitializeHemispheresUseCase(repo).execute(jid)
        messages.success(request, "✅ Planeta dividido geográficamente.")
    except Exception as e:
        messages.error(request, f"Error al dividir: {e}")
    return redirect('ver_mundo', jid=jid)

def centro_control(request):
    todas = CaosVersionORM.objects.all().order_by('-created_at')
    p, a, r, h = [], [], [], []
    for v in todas:
        l = len(v.world.id)
        niv = 1 if l==2 else (2 if l==4 else l//2)
        d = {'id': v.id, 'world_name': v.world.name, 'version_num': v.version_number, 'proposed_name': v.proposed_name, 'reason': v.change_log, 'date': v.created_at, 'author': v.author.username if v.author else '?', 'nivel_label': f"NIVEL {niv}"}
        if v.status == 'PENDING': p.append(d)
        elif v.status == 'APPROVED': a.append(d)
        elif v.status == 'REJECTED': r.append(d)
        elif v.status in ['ARCHIVED', 'LIVE']: h.append(d)
    return render(request, 'control_panel.html', {'pendientes': p, 'aprobados': a, 'rechazados': r, 'archivados': h})

def revisar_version(request, version_id):
    try: v = CaosVersionORM.objects.get(id=version_id); w = v.world
    except: return redirect('centro_control')
    imgs = get_world_images(w.id)
    bread = generate_breadcrumbs(w.id)
    len_h = len(w.id)+2 if len(w.id)<32 else len(w.id)+4
    hijos = [{'id':h.id, 'name':h.name, 'code':eclai_core.encode_eclai126(h.id), 'img':(get_world_images(h.id)[0]['url'] if get_world_images(h.id) else None)} for h in CaosWorldORM.objects.filter(id__startswith=w.id, id__regex=r'^.{'+str(len_h)+r'}$')]
    context = {'name': v.proposed_name, 'description': v.proposed_description, 'jid': w.id, 'status': f"PREVIEW v{v.version_number}", 'code_entity': eclai_core.encode_eclai126(w.id), 'nid_lore': w.id_lore if w.id_lore else f"{w.id}L01", 'imagenes': imgs, 'hijos': hijos, 'breadcrumbs': bread, 'is_preview': True, 'version_id': v.id, 'change_log': v.change_log, 'author': v.author.username if v.author else '?'}
    context['metadata'] = json.dumps(w.metadata, indent=2) if w.metadata else "{}"
    context['metadata_obj'] = w.metadata
    return render(request, 'ficha_mundo.html', context)

def ver_mundo(request, jid):
    repo = DjangoCaosRepository()
    if request.method == 'POST':
        if 'edit_mode' in request.POST: return editar_mundo(request, jid)
        child_name = request.POST.get('child_name')
        child_type = request.POST.get('child_type')
        if child_name:
            if child_type == 'ENTITY' and request.POST.get('use_ai') == 'on':
                try: GenerateCreatureUseCase(repo, Llama3Service(), StableDiffusionService()).execute(jid)
                except: pass
            else:
                nid = CreateChildWorldUseCase(repo).execute(jid, child_name, request.POST.get('child_desc'))
                if request.POST.get('use_ai') == 'on':
                    try: GenerateWorldLoreUseCase(repo, Llama3Service()).execute(nid)
                    except: pass
                    try: GenerateWorldMapUseCase(repo, StableDiffusionService()).execute_single(nid)
                    except: pass
            return redirect('ver_mundo', jid=jid)

    try: w = CaosWorldORM.objects.get(id=jid)
    except: return render(request, '404.html', {"jid": jid})

    props = w.versiones.filter(status='PENDING').order_by('-created_at')
    historial = w.versiones.exclude(status='PENDING').order_by('-version_number')[:10]
    
    len_h = len(jid)+2 if len(jid)<32 else len(jid)+4
    hijos = []
    for h in CaosWorldORM.objects.filter(id__startswith=jid, id__regex=r'^.{'+str(len_h)+r'}$'):
        short = h.id[len(jid):]
        hijos.append({'id': h.id, 'name': h.name, 'short': short, 'img':(get_world_images(h.id)[0]['url'] if get_world_images(h.id) else None)})
    
    imgs = get_world_images(jid)
    bread = generate_breadcrumbs(jid)

    meta_str = json.dumps(w.metadata, indent=2) if w.metadata else "{}"
    last_live = w.versiones.filter(status='LIVE').order_by('-created_at').first()
    date_live = last_live.created_at if last_live else w.created_at

    context = {
        'name': w.name, 'description': w.description, 'jid': jid,
        'status': w.status, 'version_live': w.current_version_number,
        'author_live': getattr(w, 'current_author_name', 'Sistema'),
        'created_at': w.created_at, 'updated_at': date_live,
        'visible': w.visible_publico,
        'code_entity': eclai_core.encode_eclai126(jid),
        'nid_lore': w.id_lore if w.id_lore else f"{jid}L01",
        'metadata': meta_str, 
        'metadata_obj': w.metadata, 
        'imagenes': imgs, 'hijos': hijos, 'breadcrumbs': bread, 
        'propuestas': props, 'historial': historial
    }
    return render(request, 'ficha_mundo.html', context)

def home(request):
    if request.method == 'POST':
        repo = DjangoCaosRepository()
        jid = CreateWorldUseCase(repo).execute(request.POST.get('world_name'), request.POST.get('world_desc'))
        return redirect('ver_mundo', jid=jid)
    
    ms = CaosWorldORM.objects.all().order_by('id')
    l = []
    for m in ms:
        imgs = get_world_images(m.id)
        cover = None
        
        # 1. LÓGICA DE PORTADA INTELIGENTE
        if m.metadata and 'cover_image' in m.metadata:
            # Buscamos si el archivo favorito existe en la lista real
            target = m.metadata['cover_image']
            found = next((i for i in imgs if i['filename'] == target), None)
            if found:
                cover = found['url']
        
        # 2. FALLBACK (Si no hay favorita o se rompió, usa la primera)
        if not cover and imgs:
            cover = imgs[0]['url']
            
        l.append({
            'id': m.id, 
            'name': m.name, 
            'status': m.status, 
            'code': eclai_core.encode_eclai126(m.id), 
            'img_file': cover, 
            'has_img': bool(cover)
        })
    
    return render(request, 'index.html', {'mundos': l})

def restaurar_version(request, version_id):
    try:
        RestoreVersionUseCase().execute(version_id, get_current_user(request))
    except Exception as e:
        print(f"Error restaurando: {e}")
    
    # Redirigimos al mundo para que veas la nueva propuesta pendiente
    # Necesitamos el ID del mundo, lo sacamos de la versión
    v = CaosVersionORM.objects.get(id=version_id)
    return redirect('ver_mundo', jid=v.world.id)