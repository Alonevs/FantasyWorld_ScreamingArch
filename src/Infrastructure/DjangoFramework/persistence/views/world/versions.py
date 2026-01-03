"""
Gestión de versiones y comparaciones.
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
        
        # --- FIX: VISUALIZAR PROPUESTA DE PORTADA ---
        proposed_cover = v.cambios.get('cover_image') if v.cambios else None
        
        if proposed_cover:
            # 1. Reset all covers first (Proposed takes precedence)
            for img in imgs: img['is_cover'] = False

            # 2. Use centralized cover detection
            from src.Infrastructure.DjangoFramework.persistence.utils import find_cover_image
            match = find_cover_image(proposed_cover, imgs)
            
            if match:
                match['is_cover'] = True
                print(f"[DEBUG] Comparar: Marked {match['filename']} as cover (Proposed: {proposed_cover})")
            else:
                print(f"[DEBUG] Comparar: No match found for {proposed_cover}")
        # --------------------------------------------
        
        # Metadata Handling for Preview
        proposed_meta = v.cambios.get('metadata', {}) if v.cambios else {}
        live_meta = w.metadata if w.metadata else {}
        
        # Calculate Metadata Version
        # Count all previous versions of this world that had metadata changes
        meta_count = CaosVersionORM.objects.filter(
            world=w, 
            version_number__lte=v.version_number
        ).filter(
            Q(cambios__has_key='metadata') | Q(cambios__action='METADATA_UPDATE')
        ).count()
        
        # Special case: if this version doesn't have metadata changes but we are previewing it,
        # we still show the metadata at that point in time (V count).
        
        # Prepare Decorated Metadata List for Template
        # v.cambios might have 'metadata' key (which is a dict with 'properties')
        proposed_meta = v.cambios.get('metadata', {}) if v.cambios else {}
        live_meta = w.metadata if w.metadata else {}
        
        from .view_utils import get_metadata_properties_dict
        proposed_props = get_metadata_properties_dict(proposed_meta)
        live_props = get_metadata_properties_dict(live_meta)
        
        diff_results = get_metadata_diff(live_meta, proposed_meta) if proposed_meta else []
        diff_map = {d['key']: d for d in diff_results}
        
        metadata_list = []
        # If we have a proposal, show it with decorations 
        # (Fall back to live properties for those not changed if it was an update? 
        # Actually usually it's a full replacement in this system).
        
        # We decide what to show based on all available keys
        all_keys = sorted(set(proposed_props.keys()) | set(live_props.keys()))
        
        for key in all_keys:
            action = diff_map.get(key, {}).get('action', 'NORMAL')
            val = proposed_props.get(key, live_props.get(key))
            
            # If it was deleted, show old value
            if action == 'DELETE':
                val = live_props.get(key)
                
            metadata_list.append({
                'key': key,
                'value': val,
                'action': action
            })
            
        # Prepare Context with Permissions
        is_admin, is_team_member = get_admin_status(request.user)
        
        context = {
            'name': v.proposed_name,
            'description': v.proposed_description,
            'jid': jid, 'public_id': safe_pid,
            'status': f"PREVIEW v{v.version_number} ({v.status})",
            'version_live': w.current_version_number,
            'author_live': v.author.username if v.author else "Desconocido",
            'created_at': v.created_at, 'updated_at': v.created_at,
            'visible': False, 
            'nid_lore': w.id_lore,
            'metadata_obj': {'properties': metadata_list},
            'metadata_version': f"V{meta_count}" if meta_count > 0 else "V0",
            'is_preview': True, 
            'preview_version_id': v.id,
            'breadcrumbs': generate_breadcrumbs(jid),
            'imagenes': imgs, 'hijos': [],
            
            # Permisos y Estados para UI
            'status_str': 'PREVIEW',
            'author_live_user': v.author,
            'is_author': is_author_or_team,
            'is_admin_role': is_admin,
            'can_edit': False, # No editar durante previsualización
            'allow_proposals': False, # No proponer sobre una previsualización
            'user_role': request.user.profile.rank_value if hasattr(request.user, 'profile') else 0
        }
        
        # --- INYECCIÓN DE ETIQUETA DE JERARQUÍA ---
        context['hierarchy_label'] = get_readable_hierarchy(jid)
        # ------------------------------------------
        
        messages.info(request, f"👀 Viendo PREVISUALIZACIÓN de versión {v.version_number}")
        return render(request, 'ficha_mundo.html', context)
    except Exception as e: 
        print(e)
        return redirect('home')
