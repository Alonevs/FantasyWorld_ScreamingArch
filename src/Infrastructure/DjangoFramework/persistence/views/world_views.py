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
# IMPORTE Q
from django.db.models import Q
from django.http import Http404
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.generate_creature_usecase import GenerateCreatureUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
from django.contrib.auth.decorators import login_required, user_passes_test
from src.FantasyWorld.Domain.Services.EntityService import EntityService
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Application.toggle_visibility import ToggleWorldVisibilityUseCase
from src.WorldManagement.Caos.Application.toggle_lock import ToggleWorldLockUseCase
from src.WorldManagement.Caos.Application.get_world_tree import GetWorldTreeUseCase
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs, get_world_images
from .view_utils import resolve_jid_orm, check_world_access, get_admin_status


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

# Removed local resolve_jid, using resolve_jid_orm instead

from django.db.models.functions import Length

def home(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        repo = DjangoCaosRepository()
        # For creation, author is current user
        try:
            jid = CreateWorldUseCase(repo).execute(request.POST.get('world_name'), request.POST.get('world_desc'))
            w = CaosWorldORM.objects.get(id=jid)
            w.author = request.user
            w.save()
            messages.success(request, "✨ Mundo propuesto. Ve al Dashboard para aprobarlo.")
        except Exception as e:
            messages.error(request, f"Error al proponer mundo: {str(e)}")
            
        return redirect('dashboard')
    
    # Show LIVE worlds (and DRAFTS for Author/Superuser)
    # 1. Base: Exclude deleted, invalid, and DRAFTS (Strict Workflow)
    ms = CaosWorldORM.objects.filter(is_active=True).exclude(status='DELETED').exclude(status='DRAFT') \
        .exclude(description__isnull=True).exclude(description__exact='') \
        .exclude(description__iexact='None') \
        .exclude(id__endswith='00', name__startswith='Nexo Fantasma') \
        .exclude(id__endswith='00', name__startswith='Ghost') \
        .exclude(id__endswith='00', name='Placeholder') \
        .select_related('born_in_epoch', 'died_in_epoch') \
        .prefetch_related('versiones', 'narrativas') \
        .order_by('id')

    # 2. Visibility Logic
    if request.user.is_superuser:
        pass # All
    elif request.user.is_authenticated:
        # User sees: LIVE OR (Their OWN content)
        # We now use 'OFFLINE' for private content instead of 'DRAFT'
        ms = ms.filter(Q(status='LIVE') | Q(author=request.user))
    else:
        # Anonymous: Only LIVE
        ms = ms.filter(status='LIVE')

    # REPRESENTATIVE LOGIC:
    # 1. Group by "Real Trunk" (Recursively strip '00' from parent).
    # 2. Sort candidates by:
    #    A. Is Real? (Prefer '0101' over '010013') -> heuristic: '00' in id?
    #    B. Level (Shallowest first)
    #    C. ID (Lowest first)
    
    candidates_by_group = {}
    
    for m in ms:
        # 1. Calculate Group Key (The nearest Real Parent)
        pid = m.id[:-2]
        while pid and pid.endswith('00'):
            pid = pid[:-2]
        
        if pid not in candidates_by_group:
            candidates_by_group[pid] = []
        candidates_by_group[pid].append(m)
    
    # 2. Pick Winner per Group
    final_list = []
    for pid, candidates in candidates_by_group.items():
        # Sort Key: (Has '00'?, Length, ID)
        # We want: No '00' first (False < True), Shorter Length first, Lower ID first.
        candidates.sort(key=lambda x: ('00' in x.id, len(x.id), x.id))
        final_list.append(candidates[0])

    # Sort final list by ID for display order
    final_list.sort(key=lambda x: x.id)

    l = []
    background_images = []
    for m in final_list:
        # Pass world_instance=m to avoid re-fetching metadata from DB (N+1 fix)
        imgs = get_world_images(m.id, world_instance=m)
        cover = imgs[0]['url'] if imgs else None
        if m.metadata and 'cover_image' in m.metadata:
            target = m.metadata['cover_image']
            found = next((i for i in imgs if i['filename'] == target), None)
            if found: cover = found['url']
        
        if cover:
            background_images.append(cover)

        # Collect up to 5 images for the slideshow
        entity_images = [i['url'] for i in imgs][:5] if imgs else []

        pid = m.public_id if m.public_id else m.id
        l.append({
            'id': m.id, 
            'public_id': pid, 
            'name': m.name, 
            'status': m.status, 
            'img_file': cover,
            'img': cover, # Fallback/Primary key to prevent VariableDoesNotExist in template
            'images': entity_images, 
            'has_img': bool(cover), 
            'visible': m.visible_publico,
            'is_locked': m.status == 'LOCKED',
            'author': m.author,
        })
    
    # Shuffle backgrounds for variety? Optional.
    import random
    random.shuffle(background_images)
    
    # Return all images (unrestricted)
    return render(request, 'index.html', {'mundos': l, 'background_images': background_images[:10]}) # Limit to 10 to save bandwidth

def ver_mundo(request, public_id):
    w_orm = resolve_jid_orm(public_id)
    if not w_orm:
        return render(request, '404.html', {"jid": public_id}, status=404)
    
    can_access, is_author_or_team = check_world_access(request, w_orm)
    if not can_access:
        return render(request, 'private_access.html', status=403)
    
    repo = DjangoCaosRepository()
    
    # 1. Handle POST (Creation)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        # Resolve ID for parent (needed for creation)
        w = resolve_jid_orm(public_id)
        if not w: return redirect('home') # Should handle better
        
        # --- SECURITY CHECK ---
        # Allow proposals from any authenticated user (Status will be PENDING)
        # We removed the strict check_ownership() here to enable the "Suggestion/Proposal" workflow.
        # ----------------------

        jid = w.id
        safe_pid = w.public_id if w.public_id else jid

        c_name = request.POST.get('child_name')
        if c_name:
            c_desc = request.POST.get('child_desc', "")
            reason = request.POST.get('reason', "Creación vía Wizard")
            use_ai = request.POST.get('use_ai_gen') == 'on'
            
            # Extract target_level (Fix UnboundLocalError)
            target_level_str = request.POST.get('target_level')
            target_level = int(target_level_str) if target_level_str else None
            
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

    # --- URL CANONICALIZATION (Legacy ID -> NanoID) ---
    # If accessed via legacy ID (e.g., '01') but entity has a public_id (NanoID), redirect.
    # We check if the requested 'public_id' mismatches the resolved 'context["public_id"]'.
    if context['public_id'] and context['public_id'] != public_id:
        return redirect('ver_mundo', public_id=context['public_id'])
    # --------------------------------------------------

    # --- HIERARCHY LABEL INJECTION ---
    context['hierarchy_label'] = get_readable_hierarchy(context['jid'])
    context['status_str'] = w_orm.status
    context['author_live_user'] = w_orm.author
    
    # PERMISSIONS CHECK
    is_admin, is_team_member = get_admin_status(request.user)

    context['is_author'] = is_author_or_team or is_team_member
    context['can_edit'] = is_author_or_team or is_team_member
    context['allow_proposals'] = is_team_member
    context['is_admin_role'] = is_admin
    # ---------------------------------
    # ---------------------------------
    
    # --- DEEP CREATION OPTIONS ---
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_available_levels
    context['available_levels'] = get_available_levels(context['jid'])
    # -----------------------------

    # --- METADATA ADAPTER (V2.0 + V1.0 Support) ---
    # Ensure frontend always gets a flat list of properties
    raw_meta = context.get('metadata_obj', {})
    if not isinstance(raw_meta, dict): raw_meta = {} # Safety check
    
    properties = []
    
    # CASE C: V2.1 "Standard List" (Auto-Noos & Manual Format)
    if 'properties' in raw_meta and isinstance(raw_meta['properties'], list):
         properties = raw_meta['properties']

    # CASE A: V2.0 Structured (Schema-based - Legacy/Imported)
    elif 'datos_nucleo' in raw_meta:
        # 1. Type
        if 'tipo_entidad' in raw_meta:
            properties.append({'key': 'TIPO_ENTIDAD', 'value': raw_meta['tipo_entidad']})
            
        # 2. Nucleo (Fixed)
        for k, v in raw_meta.get('datos_nucleo', {}).items():
            properties.append({'key': k, 'value': v})
            
        # 3. Extended (Extra)
        for k, v in raw_meta.get('datos_extendidos', {}).items():
            properties.append({'key': k, 'value': v})
            
    # CASE B: V1.0 Flat (Legacy)
    else:
        for k, v in raw_meta.items():
            # Filter out internal/system keys if any
            if k not in ['cover_image', 'images', 'properties']: 
                properties.append({'key': k, 'value': v})
                
    context['metadata_obj'] = {'properties': properties}
    # ----------------------------------------------

    return render(request, 'ficha_mundo.html', context)

@login_required
def editar_mundo(request, jid):
    repo = DjangoCaosRepository()
    w_domain = resolve_world_id(repo, jid)
    if not w_domain: return redirect('home')
    real_jid = w_domain.id.value
    w_orm = CaosWorldORM.objects.get(id=real_jid)

    # --- SECURITY CHECK ---
    # We remove strict check_ownership() to allow PROPOSALS from any authenticated user.
    # The actual edit action (ProposeChangeUseCase) is safe (PENDING status).
    # ----------------------

    # LOCK CHECK (Block edits if locked, unless Superuser)
    if w_orm.status == 'LOCKED' and not request.user.is_superuser:
        messages.error(request, "⛔ Este mundo está BLOQUEADO por la Administración. No se permiten ediciones.")
        return redirect('ver_mundo', public_id=w_orm.public_id if w_orm.public_id else w_orm.id)

    if request.method == 'POST':
        try:
            w = resolve_jid_orm(jid); real_jid = w.id if w else jid
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
                
                print(f"📝 [Manual Edit] Submitting Metadata Proposal: {len(metadata_prop['properties'])} items.")
                print(f"   Payload: {metadata_prop}")
                
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

def get_entity_smart(identifier):
    """Ayuda a encontrar la entidad ya sea por ID (int) o Code (str)"""
    # 1. Intentar por CÓDIGO (NanoID)
    entity = CaosWorldORM.objects.filter(public_id=identifier).first()
    if entity:
        return entity
    # 2. Intentar por ID (Legacy)
    # En este proyecto el ID es CharField, así que buscamos directo
    return CaosWorldORM.objects.filter(id=identifier).first()

@login_required
def toggle_entity_status(request, jid):
    w = get_entity_smart(jid)
    if not w:
        raise Http404("Entidad no encontrada")

    # 1. Verificar Permisos (Superuser o Autor)
    if request.user.is_superuser or w.author == request.user:
        # 2. Cambiar Estado
        if w.status == 'LIVE':
            w.status = 'OFFLINE'
        else:
            w.status = 'LIVE'
        w.save()
        messages.success(request, f"Estado actualizado a: {w.status}")
    else:
        messages.error(request, "Permiso denegado.")

    # 3. REDIRECCIÓN ROBUSTA
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def borrar_mundo(request, jid): 
    try: 
        # Robust Lookup
        w = CaosWorldORM.objects.filter(Q(id=jid) | Q(public_id=jid)).first()
        if not w: w = get_object_or_404(CaosWorldORM, id=jid)
        
        check_ownership(request.user, w) # Security Check
        
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

@login_required
def toggle_visibilidad(request, jid):
    try: 
        repo = DjangoCaosRepository()
        w_domain = resolve_world_id(repo, jid)
        w = CaosWorldORM.objects.get(id=w_domain.id.value)
        check_ownership(request.user, w) # Security Check
        
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

@login_required
def init_hemisferios(request, jid):
    try: 
        w=resolve_jid_orm(jid)
        w_orm = CaosWorldORM.objects.get(id=w.id)
        check_ownership(request.user, w_orm)
        InitializeHemispheresUseCase(DjangoCaosRepository()).execute(w.id); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')

def escanear_planeta(request, jid): return redirect('ver_mundo', public_id=jid)

def mapa_arbol(request, public_id):
    try:
        repo = DjangoCaosRepository()
        # Security Check
        w_orm = resolve_jid_orm(public_id)
        if not w_orm: return redirect('home')
        is_live = (w_orm.status == 'LIVE')
        is_author = (request.user.is_authenticated and w_orm.author == request.user)
        is_superuser = request.user.is_superuser
        if not (is_live or is_author or is_superuser): 
             return render(request, 'private_access.html', status=403)

        result = GetWorldTreeUseCase(repo).execute(public_id)
        if not result: return redirect('home')
        return render(request, 'mapa_arbol.html', result)
    except Http404: raise
    except: return redirect('ver_mundo', public_id=public_id)

@login_required
def toggle_lock(request, jid):
    # Solo Superuser puede bloquear
    if not request.user.is_superuser:
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    w_orm = get_entity_smart(jid)
    if not w_orm:
        raise Http404("Entidad no encontrada")
    
    # Lógica de Bloqueo
    if w_orm.status == 'LOCKED':
        w_orm.status = 'OFFLINE' # Desbloquear a estado seguro
        messages.success(request, "🔓 Mundo desbloqueado (OFFLINE).")
    else:
        w_orm.status = 'LOCKED'
        messages.warning(request, "🔒 Mundo BLOQUEADO.")
    
    w_orm.save()
    
    # CRÍTICO: Redirigir a la página desde donde se hizo clic
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# @login_required (Removed for Public Live Access)
def ver_metadatos(request, public_id):
    w = resolve_jid_orm(public_id)
    if not w: return redirect('home')

    # Security Check
    is_live = (w.status == 'LIVE')
    is_author = (request.user.is_authenticated and w.author == request.user)
    is_superuser = request.user.is_superuser
    if not (is_live or is_author or is_superuser): 
        return render(request, 'private_access.html', status=403)
    
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

# --- AUTO-NOOS API ---
@csrf_exempt 
def api_auto_noos(request, jid):
    try:
        print(f"🤖 [Auto-Noos] Start for JID: {jid}")
        repo = DjangoCaosRepository()
        w_domain = resolve_world_id(repo, jid)
        
        if not w_domain:
            return JsonResponse({'status': 'error', 'message': 'Mundo no encontrado'})
        
        # 1. Gather Context
        sources_found = []
        context_parts = [f"Entidad: {w_domain.name}"]
        
        # A. Description
        # FIX: Domain Entity uses lore_description, ORM uses description.
        # Check both to be safe (Hybrid Object)
        desc_val = getattr(w_domain, 'lore_description', '') or getattr(w_domain, 'description', '')
        if desc_val and len(desc_val.strip()) > 5:
            context_parts.append(f"Descripción: {desc_val}")
            sources_found.append("Descripción")
            
        # B. Existing Metadata
        try:
            w_orm = CaosWorldORM.objects.get(id=w_domain.id.value)
            raw_meta = w_orm.metadata or {}
            if isinstance(raw_meta, dict):
                 # Flatten existing dict if any suitable
                 if 'properties' in raw_meta and raw_meta['properties']:
                     context_parts.append(f"Metadatos Existentes: {json.dumps(raw_meta['properties'])}")
                     sources_found.append("Metadatos")
        except Exception as e:
            print(f"⚠️ Error reading existing metadata: {e}")
        
        # C. Narratives
        try:
            narrs = w_orm.narrativas.filter(is_active=True).order_by('-updated_at')[:5]
            if narrs.exists():
                narr_text = "\nInformación Narrativa:\n"
                has_narr = False
                for n in narrs:
                    if n.contenido and len(n.contenido.strip()) > 10:
                        narr_text += f"- {n.titulo}: {n.contenido[:400]}...\n"
                        has_narr = True
                if has_narr:
                    context_parts.append(narr_text)
                    sources_found.append("Narrativa")
        except Exception as e:
            print(f"⚠️ Error reading narratives: {e}")

        if not sources_found:
             # FALLBACK: If almost no context, force creative generation based on Name
             print("⚠️ Low context. Engaging Creative Mode.")
             context_text = f"Entidad: {w_domain.name}\n(Esta entidad no tiene descripción. INVENTA atributos coherentes con un mundo de fantasía basados en su nombre)."
        else:
             context_text = "\n\n".join(context_parts)

        # 2. RESOLVE SCHEMA (Source of Truth: metadata_router.py)
        try:
            from src.WorldManagement.Caos.Domain.metadata_router import get_schema_for_hierarchy
            
            raw_id = w_domain.id.value
            level = len(raw_id) // 2
            
            target_schema = get_schema_for_hierarchy(raw_id, level)
            
            if target_schema:
                print(f"📏 [Auto-Noos] Using Strict Schema for Level {level} (JID {raw_id})")
            else:
                print(f"ℹ️ [Auto-Noos] No explicit schema for Level {level} (Generic Mode)")

        except Exception as e:
            print(f"⚠️ Schema Resolution Failed: {e}")

        # 3. Prompt Engineering
        system_prompt = (
            "Eres el Oráculo del Caos (Auto-Noos). Extrae metadatos del texto.\n"
            "Devuelve SOLO JSON con formato: { \"properties\": [ {\"key\": \"Nombre\", \"value\": \"Valor\"} ] }.\n"
        )

        # 3. Prompt Engineering (Concise Mode)
        base_system_prompt = (
            "Eres un Motor de Base de Datos Semántica para Worldbuilding.\n"
            "Tu objetivo es extraer atributos técnicos de una narrativa para rellenar una ficha JSON.\n\n"
            "REGLAS ABSOLUTAS DE FORMATO:\n"
            "1. LONGITUD MÁXIMA: Los valores deben tener entre 1 y 3 palabras. NUNCA frases completas.\n"
            "   - ⛔ MALO: 'El clima es muy seco con tormentas de arena'\n"
            "   - ✅ BUENO: 'Árido / Tormentoso'\n"
            "2. ESTILO: Usa un tono técnico, científico o de RPG. Sé directo.\n"
            "3. VALORES PROHIBIDOS: No uses 'TRUE', 'FALSE', 'SI', 'NO' ni copies los ejemplos. Interpreta el texto.\n"
            "   - Si el esquema dice 'leyes_fisicas', no ponas 'TRUE'. Pon 'Inestables', 'Rígidas', 'Mágicas'.\n"
            "4. DATOS EXTRA: Si detectas conceptos únicos (razas, materiales, dioses), añádelos como claves nuevas, manteniendo el valor corto.\n"
            "5. TU SALIDA DEBE SER SOLO EL JSON LIMPIO."
        )

        if target_schema and 'campos_fijos' in target_schema:
            fixed = json.dumps(target_schema['campos_fijos'], ensure_ascii=False)
            system_prompt = base_system_prompt + f"\n\n⚠️ ESQUEMA OBLIGATORIO: Debes priorizar y rellenar estos campos: {fixed}."
        else:
            system_prompt = base_system_prompt + "\n\nTAREA: Extrae los 5-10 atributos técnicos/sociológicos más críticos para definir esta entidad."

        user_prompt = f"Analiza este texto narrativo:\n\n{context_text}"
        
        # 4. AI Call (Using Structured Chat API)
        print(f"🤖 Sending Prompt to AI ({len(user_prompt)} chars). Max Tokens: 200")
        
        # Use generate_structure with strict token limit to enforce conciseness
        data = Llama3Service().generate_structure(system_prompt, user_prompt, max_tokens=200)
        
        print(f"📥 AI Response Data: {str(data)[:100]}...")

        if not data:
             return JsonResponse({'status': 'error', 'message': 'La IA no devolvió datos válidos.'})

        # 5. Parse/Normalize (Data is already a dict)
        properties = []
        
        # Normalize
        if 'properties' in data and isinstance(data['properties'], list):
            properties = data['properties']
        else:
            # Flat dict fallback
            exclude = ['properties', 'datos_nucleo', 'datos_extendidos', 'tipo_entidad']
            # Check for nested schema structure
            if 'datos_nucleo' in data:
                for k,v in data.get('datos_nucleo', {}).items(): properties.append({'key': k, 'value': str(v)})
                for k,v in data.get('datos_extendidos', {}).items(): properties.append({'key': k, 'value': str(v)})
            else:
                for k,v in data.items():
                    if k not in exclude and not isinstance(v, dict):
                        properties.append({'key': k, 'value': str(v)})
    
        if not properties:
            return JsonResponse({'status': 'error', 'message': 'La IA no extrajo datos válidos.'})

        return JsonResponse({'status': 'success', 'properties': properties})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f"Server Error: {str(e)}"})

