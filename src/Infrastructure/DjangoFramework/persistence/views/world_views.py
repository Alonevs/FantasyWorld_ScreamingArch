import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosNarrativeORM, CaosEventLog, MetadataTemplate
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.generate_creature_usecase import GenerateCreatureUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
from src.FantasyWorld.Domain.Services.EntityService import EntityService
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Application.toggle_visibility import ToggleWorldVisibilityUseCase
from src.WorldManagement.Caos.Application.toggle_lock import ToggleWorldLockUseCase
from src.WorldManagement.Caos.Application.get_world_tree import GetWorldTreeUseCase
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs, get_world_images


from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy

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

from django.db.models.functions import Length

def home(request):
    if request.method == 'POST':
        repo = DjangoCaosRepository()
        jid = CreateWorldUseCase(repo).execute(request.POST.get('world_name'), request.POST.get('world_desc'))
        messages.success(request, "✨ Mundo propuesto. Ve al Dashboard para aprobarlo.")
        return redirect('dashboard')
    
    # Show ALL live worlds that have CONTENT (Description is not empty)
    # This hides "gap" levels or empty containers, but shows deep entities like "Plataforma 1º"
    ms = CaosWorldORM.objects.exclude(status='DRAFT').exclude(description__isnull=True).exclude(description__exact='').exclude(description__iexact='None').order_by('id')
    l = []
    for m in ms:
        imgs = get_world_images(m.id)
        cover = imgs[0]['url'] if imgs else None
        if m.metadata and 'cover_image' in m.metadata:
            target = m.metadata['cover_image']
            found = next((i for i in imgs if i['filename'] == target), None)
            if found: cover = found['url']
        
        pid = m.public_id if m.public_id else m.id
        l.append({'id': m.id, 'public_id': pid, 'name': m.name, 'status': m.status, 'img_file': cover, 'has_img': bool(cover)})
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
        target_level_str = request.POST.get('target_level')
        target_level = int(target_level_str) if target_level_str else None
        
        if c_name:
            c_desc = request.POST.get('child_desc', "")
            reason = request.POST.get('reason', "Creación vía Wizard")
            use_ai = request.POST.get('use_ai_gen') == 'on'
            
            # Use EntityService for unified creation
            service = EntityService()
            new_id = service.create_entity(
                parent_id=jid, 
                name=c_name, 
                description=c_desc, 
                reason=reason, 
                generate_image=use_ai, 
                target_level=target_level
            )
            
            try:
                if target_level and target_level > (len(jid)//2 + 1):
                     messages.success(request, f"✨ Entidad profunda creada con Salto (Nivel {target_level}).")
                else:
                     messages.success(request, "✨ Entorno propuesto (y su imagen). Ve al Dashboard para aprobarlo.")
                return redirect('dashboard')
            except:
                return redirect('dashboard')

    # 2. Handle GET (Display) via Use Case
    context = GetWorldDetailsUseCase(repo).execute(public_id, request.user)
    
    if not context:
        return render(request, '404.html', {"jid": public_id})

    # --- HIERARCHY LABEL INJECTION ---
    context['hierarchy_label'] = get_readable_hierarchy(context['jid'])
    # ---------------------------------
    
    # --- DEEP CREATION OPTIONS ---
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_available_levels
    context['available_levels'] = get_available_levels(context['jid'])
    # -----------------------------

    # --- POC METADATA SYSTEM ---
    # Detectar si estamos viendo el Caos (Root) o check manual
    # Para POC: Si el ID es 0, O el nombre contiene "Caos" (ignorando mayúsculas)
    w_name = context.get('name', '')
    if public_id == "0" or "Caos" in w_name or "chaos" in w_name.lower():
        try:
            tpl = MetadataTemplate.objects.filter(entity_type='CHAOS').first()
            if tpl:
                context['metadata_template'] = {
                    'entity_type': tpl.entity_type,
                    'schema': tpl.schema_definition,
                    'ui': tpl.ui_config
                }
        except Exception as e:
            print(f"⚠️ [POC] Error cargando plantilla: {e}")
    # ---------------------------

    return render(request, 'ficha_mundo.html', context)

def editar_mundo(request, jid):
    if request.method == 'POST':
        try:
            w = resolve_jid(jid); real_jid = w.id if w else jid
            desc = request.POST.get('description')
            action_type = request.POST.get('action_type', 'EDIT_WORLD')
            
            metadata_prop = None
            reason = request.POST.get('reason', 'Actualización de Metadatos')

            # Handle Metadata Proposal
            if action_type == 'METADATA_PROPOSAL':
                # NEW DYNAMIC LOGIC (Arrays)
                prop_keys = request.POST.getlist('prop_keys[]')
                prop_values = request.POST.getlist('prop_values[]')
                
                metadata_prop = {'properties': []}
                
                # Zip them together
                if prop_keys and prop_values:
                    for k, v in zip(prop_keys, prop_values):
                        if k.strip(): # Ignore empty keys
                            metadata_prop['properties'].append({'key': k.strip(), 'value': v.strip()})
                
                # If editing metadata, we might keep name/desc as is (or use hidden fields)
                # For safety, let's just pass None to keep existing values in UseCase
                ProposeChangeUseCase().execute(real_jid, None, None, reason, get_current_user(request), metadata_proposal=metadata_prop)
                messages.success(request, f"🔮 Propuesta de METADATOS enviada (v{CaosVersionORM.objects.filter(world_id=real_jid).count() + 1}).")
                log_event(request.user, "PROPOSE_METADATA", real_jid, f"Reason: {reason}")
            else:
                # Regular Edit
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
        
        # Determine next version number
        last_v = w.versiones.order_by('-version_number').first()
        next_v = (last_v.version_number + 1) if last_v else 1
        
        # Create DELETE Proposal
        CaosVersionORM.objects.create(
            world=w,
            proposed_name=w.name,
            proposed_description=w.description,
            version_number=next_v,
            status='PENDING',
            change_log="Solicitud de Eliminación",
            cambios={'action': 'DELETE'},
            author=get_current_user(request)
        )
        
        messages.warning(request, "🗑️ Solicitud de eliminación creada. Ve al Dashboard para confirmar.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error requesting delete: {e}")
        return redirect('home')

def toggle_visibilidad(request, jid):
    try: 
        repo = DjangoCaosRepository()
        w_domain = resolve_world_id(repo, jid)
        w = CaosWorldORM.objects.get(id=w_domain.id.value)
        
        next_v = CaosVersionORM.objects.filter(world=w).count() + 1
        current_vis = w.visible_publico
        target_vis = not current_vis
        
        CaosVersionORM.objects.create(
            world=w,
            proposed_name=w.name,
            proposed_description=w.description,
            version_number=next_v,
            status='PENDING',
            change_log=f"Solicitud cambio visibilidad: {'PÚBLICO' if target_vis else 'PRIVADO'}",
            cambios={'action': 'TOGGLE_VISIBILITY', 'target_visibility': target_vis},
            author=get_current_user(request)
        )
        
        messages.success(request, "👁️ Solicitud de cambio de visibilidad creada.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error toggling visibility: {e}")
        return redirect('home')

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
            'visible': False, 
            'nid_lore': w.id_lore, 'metadata': meta_str, 
            'metadata_obj': w.metadata, 'imagenes': imgs, 'hijos': [], 
            'breadcrumbs': generate_breadcrumbs(jid), 
            'is_preview': True, 
            'preview_version_id': v.id
        }
        
        # --- HIERARCHY LABEL INJECTION ---
        context['hierarchy_label'] = get_readable_hierarchy(jid)
        # ---------------------------------
        
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

@login_required
def ver_metadatos(request, public_id):
    w = resolve_jid(public_id)
    if not w: return redirect('home')
    
    context = {
        'name': w.name,
        'public_id': w.public_id,
        'jid': w.id,
        'metadata_template': None
    }
    
    # --- HIERARCHY LABEL INJECTION ---
    context['hierarchy_label'] = get_readable_hierarchy(w.id)
    # ---------------------------------
    
    # Load Metadata (Reuse logic)
    if w.id == "01" or "Caos" in w.name:
         tpl = MetadataTemplate.objects.filter(entity_type='CHAOS').first()
         if tpl:
             context['metadata_template'] = {
                'entity_type': tpl.entity_type,
                'schema': tpl.schema_definition,
                # In real app, fetch stored metadata values from w.metadata
             }
             context['metadata_obj'] = {} 
    
    return render(request, 'ver_metadatos.html', context)