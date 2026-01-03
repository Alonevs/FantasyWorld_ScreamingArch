"""
Acciones sobre mundos (toggle status, borrar, etc).
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


@login_required
def toggle_entity_status(request, jid):
    w = resolve_jid_orm(jid)
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
        # Búsqueda Robusta
        # Búsqueda Robusta usando helper estandarizado
        w = resolve_jid_orm(jid)
        if not w:
            messages.error(request, "Entidad no encontrada")
            return redirect('home')
        
        check_ownership(request.user, w) # Chequeo de Seguridad
        
        # Determinar siguiente número de versión
        last_v = w.versiones.order_by('-version_number').first()
        next_v = (last_v.version_number + 1) if last_v else 1
        
        # Crear Propuesta de ELIMINACIÓN
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
        print(f"Error solicitando eliminación: {e}")
        return redirect('home')

@login_required
def toggle_visibilidad(request, jid):
    try: 
        repo = DjangoCaosRepository()
        w_domain = resolve_world_id(repo, jid)
        w = CaosWorldORM.objects.get(id=w_domain.id.value)
        check_ownership(request.user, w) # Chequeo de Seguridad
        
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
        print(f"Error cambiando visibilidad: {e}")
        return redirect('home')

@login_required
def toggle_lock(request, jid):
    
    w_orm = resolve_jid_orm(jid)
    if not w_orm:
        raise Http404("Entidad no encontrada")

    # CHEQUEO DE PERMISOS: Solo el Autor o Superusuario
    # (Admins no pueden bloquear mundos ajenos, solo Superusuarios)
    can_lock = request.user.is_superuser or (w_orm.author == request.user)
        
    if not can_lock:
        messages.error(request, "⛔ Solo el Autor o Superadmin pueden bloquear.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
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
