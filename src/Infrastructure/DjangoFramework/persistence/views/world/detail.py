"""
Vistas de detalle y lectura de mundos.
"""
import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.utils.timezone import localtime
from django.db.models import Q, Case, When, Value, IntegerField, Count
from django.db.models.functions import Length

from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, CaosVersionORM, CaosNarrativeORM, CaosEventLog, 
    MetadataTemplate, TimelinePeriodVersion, CaosLike, UserProfile, CaosComment, Message
)
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.Shared.Services.SocialService import SocialService
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.generate_creature_usecase import GenerateCreatureUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
from src.WorldManagement.Caos.Application.toggle_visibility import ToggleWorldVisibilityUseCase
from src.WorldManagement.Caos.Application.toggle_lock import ToggleWorldLockUseCase
from src.WorldManagement.Caos.Application.get_world_tree import GetWorldTreeUseCase
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs, get_world_images
from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
from src.FantasyWorld.Domain.Services.EntityService import EntityService
from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy
from ..view_utils import resolve_jid_orm, check_world_access, get_admin_status, get_metadata_diff
from .utils import log_event, get_current_user


def ver_mundo(request, public_id):
    """
    Ficha de Entidad: Muestra el Lore, Metadatos Estructurados y Galería.
    Permite la creación de entidades hijas ('Sugerencia de Creación') 
    y gestiona la normalización de metadatos para el frontend.
    """
    w_orm = resolve_jid_orm(public_id)
    if not w_orm:
        return render(request, '404.html', {"jid": public_id}, status=404)
    
    can_access, is_author_or_team = check_world_access(request, w_orm)
    if not can_access:
        return render(request, 'private_access.html', status=403)
    
    repo = DjangoCaosRepository()
    
    # 1. Manejar POST (Creación)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        # Resolver ID para el padre (necesario para la creación)
        w = resolve_jid_orm(public_id)
        if not w: return redirect('home') # Debería manejarse mejor
        
        # --- CHEQUEO DE SEGURIDAD ---
        # Permitir propuestas de cualquier usuario autenticado (Estado será PENDING)
        # Eliminamos el check_ownership() estricto aquí para habilitar el flujo de "Sugerencia/Propuesta".
        # ----------------------------

        jid = w.id
        safe_pid = w.public_id if w.public_id else jid

        c_name = request.POST.get('child_name')
        if c_name:
            c_desc = request.POST.get('child_desc', "")
            reason = request.POST.get('reason', "Creación vía Wizard")
            use_ai = request.POST.get('use_ai_gen') == 'on'
            
            target_level_str = request.POST.get('target_level')
            target_level = int(target_level_str) if target_level_str else None
            
            # Usar EntityService para creación unificada
            service = EntityService()
            new_id = service.create_entity(
                parent_id=jid, 
                name=c_name, 
                description=c_desc, 
                reason=reason, 
                generate_image=use_ai, 
                target_level=target_level,
                user=request.user
            )
            
            try:
                if target_level and target_level > (len(jid)//2 + 1):
                     messages.success(request, f"✨ Entidad profunda creada con Salto (Nivel {target_level}).")
                else:
                     messages.success(request, "✨ Entorno propuesto (y su imagen). Ve al Dashboard para aprobarlo.")
                return redirect('dashboard')
            except:
                return redirect('dashboard')

    # --- PERIOD SUPPORT (New Timeline System) ---
    from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriod
    from src.Shared.Services.TimelinePeriodService import TimelinePeriodService
    
    # Resolver Entidad ORM para el servicio de períodos
    w_orm = resolve_jid_orm(public_id)
    if not w_orm: raise Http404

    # Obtener slug del período solicitado (por defecto: 'actual')
    period_slug = request.GET.get('period', 'actual')
    
    # Obtener todos los períodos de esta entidad
    all_periods = TimelinePeriodService.get_periods_for_world(w_orm)
    
    # Obtener el período actual (ACTUAL)
    current_period = TimelinePeriodService.get_current_period(w_orm)
    
    # Determinar qué período mostrar
    if period_slug == 'actual' or not period_slug:
        viewing_period = current_period
    else:
        viewing_period = all_periods.filter(slug=period_slug).first()
        if not viewing_period:
            # Si el slug no existe, redirigir a ACTUAL
            messages.warning(request, f"Período '{period_slug}' no encontrado. Mostrando ACTUAL.")
            return redirect('ver_mundo', public_id=public_id)

    # 1.5. Check for Retouch Proposal (Period or Metadata)
    retouch_proposal = None
    prop_id = request.GET.get('proposal_id')
    if prop_id:
        # Try Period Version first
        try:
            retouch_proposal = TimelinePeriodVersion.objects.get(id=prop_id)
            messages.info(request, f"✏️ Retomando propuesta rechazada de Periodo v{retouch_proposal.version_number}. Datos cargados.")
        except TimelinePeriodVersion.DoesNotExist:
            # Try World Version
            try:
                retouch_proposal = CaosVersionORM.objects.get(id=prop_id)
                messages.info(request, f"✏️ Retomando propuesta rechazada de Mundo v{retouch_proposal.version_number}. Datos cargados.")
            except CaosVersionORM.DoesNotExist:
                pass

    # 2. Manejar GET (Visualización) mediante Caso de Uso
    # PASAMOS EL PERIOD_SLUG PARA FILTRAR IMÁGENES
    context = GetWorldDetailsUseCase(repo).execute(public_id, request.user, period_slug=period_slug)
    
    if not context:
        return render(request, '404.html', {"jid": public_id})

    # --- CANONICALIZACIÓN DE URL (ID Antiguo -> NanoID) ---
    if context['public_id'] and context['public_id'] != public_id:
        return redirect('ver_mundo', public_id=context['public_id'])
    # ------------------------------------------------------

    # Si estamos viendo un período que NO es ACTUAL, sobrescribir descripción
    if viewing_period and not viewing_period.is_current:
        context['description'] = viewing_period.description or w_orm.description
        context['is_period_view'] = True
        context['viewing_period'] = viewing_period
        
        # Sobrescribir metadatos para mostrar los del periodo
        # Sobrescribir metadatos para mostrar los del periodo
        from ..view_utils import get_metadata_properties_dict
        # Asegurar que siempre se procesen los metadatos (fallback a world si period vacío)
        target_meta = viewing_period.metadata if viewing_period.metadata else w_orm.metadata
        props = get_metadata_properties_dict(target_meta)
        context['props'] = props
        
        # FIX: Adaptar formato para _metadata_viewer.html (espera 'metadata_obj.properties')
        context['metadata_obj'] = {
            'properties': [{'key': k, 'value': v} for k, v in props.items()]
        }
        
    # Override Info Sidebar
        context['created_at'] = viewing_period.created_at
        context['version_live'] = viewing_period.current_version_number
        
        # Entity key for period-specific social interactions
        context['period_entity_key'] = f"period_{period_slug}_{public_id}"
        
        # Derivar Autor desde la primera versión del período
        first_v = viewing_period.versions.order_by('version_number').first()
        if first_v and first_v.author:
             context['author_live'] = first_v.author.username
             context['author_live_user'] = first_v.author
             context['author_name'] = first_v.author.username
             # Get avatar using centralized utility
             from src.Infrastructure.DjangoFramework.persistence.utils import get_user_avatar
             context['author_avatar_url'] = get_user_avatar(first_v.author, context['jid'])
        else:
             context['author_live'] = "Desconocido"
             context['author_name'] = "Desconocido"
             context['author_avatar_url'] = ""

    else:
        context['is_period_view'] = False
        context['viewing_period'] = current_period
        # Entity key for current period (uses world_ format)
        context['period_entity_key'] = f"world_{public_id}"
    
    # Pasar períodos al contexto para el selector
    context['timeline_periods'] = all_periods.exclude(is_current=True).order_by('order')
    context['current_period_slug'] = period_slug
    context['retouch_proposal'] = retouch_proposal # Pass the object or dict
    # ---------------------------------

    # --- INYECCIÓN DE ETIQUETA DE JERARQUÍA ---
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy, get_children_label # Importar helpers
    context['hierarchy_label'] = get_readable_hierarchy(context['jid'])
    context['children_label'] = get_children_label(context['jid']) # NUEVO: Pasar etiqueta para el grid
    context['status_str'] = w_orm.status
    context['author_live_user'] = w_orm.author
    
    # Prepare author avatar URL (same pattern as image avatars)
    from src.Infrastructure.DjangoFramework.persistence.utils import get_user_avatar
    context['author_name'] = "Alone"
    context['author_avatar_url'] = ""
    if w_orm.author:
        context['author_name'] = w_orm.author.username
        context['author_avatar_url'] = get_user_avatar(w_orm.author, context['jid'])
    
    # CHEQUEO DE PERMISOS
    # NOTA: Los permisos (can_edit, is_admin_role, etc.) ya vienen calculados 
    # robustamente desde GetWorldDetailsUseCase (que usa policies.py).
    # NO debemos sobrescribirlos aquí con lógica simplificada.
    
    # is_admin ya se calcula en el usecase como 'is_admin_role'
    # allow_proposals no se usa mucho, pero si se usara, debería venir del use case intentando unificar.
    # Por seguridad, solo inyectamos lo que NO venga del use case.
    
    if 'can_edit' not in context: # Fallback por si acaso
         context['can_edit'] = is_author_or_team
    # ---------------------------------
    
    # --- OPCIONES DE CREACIÓN PROFUNDA ---
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_available_levels
    context['available_levels'] = get_available_levels(context['jid'])
    # -------------------------------------


    # --- RETOUCH DATA PRE-FILL ---
    if retouch_proposal:
        context['is_retouch_mode'] = True
        context['retouch_proposal'] = retouch_proposal
        
        # Extract properties for metadata manager
        retouch_props = []
        if isinstance(retouch_proposal, TimelinePeriodVersion):
            meta = retouch_proposal.proposed_metadata
            if isinstance(meta, dict):
                retouch_props = [{'key': k, 'value': v} for k, v in meta.items()]
            elif isinstance(meta, list):
                retouch_props = meta
        else:
            # CaosVersionORM
            raw_props = retouch_proposal.cambios.get('metadata', {}).get('properties') or retouch_proposal.cambios.get('properties')
            if raw_props:
                retouch_props = raw_props
        
        if retouch_props:
            context['metadata_obj'] = {'properties': retouch_props}
            # Also update 'props' if it exists in context for visual consistency in viewer
            context['props'] = {p['key']: p['value'] for p in retouch_props}

    return render(request, 'ficha_mundo.html', context)

def ver_metadatos(request, public_id):
    w = resolve_jid_orm(public_id)
    if not w: return redirect('home')

    # Chequeo de Seguridad
    can_access, _ = check_world_access(request, w)
    if not can_access: 
        return render(request, 'private_access.html', status=403)
    
    context = {
        'name': w.name,
        'public_id': w.public_id,
        'jid': w.id,
        'metadata_template': None
    }
    
    # --- INYECCIÓN DE ETIQUETA DE JERARQUÍA ---
    context['hierarchy_label'] = get_readable_hierarchy(w.id)
    # ------------------------------------------
    
    # Cargar Metadatos (Reutilizar lógica)
    if w.id == "01" or "Caos" in w.name:
         tpl = MetadataTemplate.objects.filter(entity_type='CHAOS').first()
         if tpl:
             context['metadata_template'] = {
                'entity_type': tpl.entity_type,
                'schema': tpl.schema_definition,
                # En la aplicación real, recuperar los valores de metadatos almacenados de w.metadata
             }
             context['metadata_obj'] = {} 
    
    return render(request, 'ver_metadatos.html', context)

def mapa_arbol(request, public_id):
    try:
        repo = DjangoCaosRepository()
        # Chequeo de Seguridad
        w_orm = resolve_jid_orm(public_id)
        if not w_orm: return redirect('home')
        
        can_access, _ = check_world_access(request, w_orm)
        if not can_access: 
             return render(request, 'private_access.html', status=403)

        result = GetWorldTreeUseCase(repo).execute(public_id)
        if not result: return redirect('home')
        return render(request, 'mapa_arbol.html', result)
    except Http404: raise
    except: return redirect('ver_mundo', public_id=public_id)
