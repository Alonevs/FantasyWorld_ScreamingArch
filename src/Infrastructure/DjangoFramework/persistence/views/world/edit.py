"""
Vistas de edición de mundos.
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
@require_POST
def update_avatar(request):
    try:
        if 'avatar' not in request.FILES:
            return JsonResponse({'error': 'No image provided'}, status=400)
            
        file = request.FILES['avatar']
        
        # Ensure Profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Save
        profile.avatar = file
        profile.save()
        
        return JsonResponse({'status': 'ok', 'url': profile.avatar.url})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def editar_mundo(request, jid):
    """
    Editor de Entidad: Interfaz para proponer cambios de lore o metadatos técnicos.
    Implementa el flujo de propuestas 'ECLAI' y soporta el modo 'Retoque'
    para corregir versiones rechazadas.
    """
    # Usar helper robusto que intenta Dominio primero, luego PublicID/ID
    w_orm = resolve_jid_orm(jid)
    if not w_orm: return redirect('home')
    
    real_jid = w_orm.id # Ya tenemos el objeto ORM

    # Antigua lógica de retoque eliminada (movida al final para robustez del contexto)
    
    # CHEQUEO DE BLOQUEO
    # El Bypass de Admin solo debe aplicar si tiene acceso de edición legítimo.
    # Como estamos en 'editar_mundo', debemos comprobar si realmente tiene derechos.
    # Nota: 'editar_mundo' aún no llama a check_world_access. Debería.
    
    # CHEQUEO DE BLOQUEO Y PERMISOS DE EDICIÓN
    from src.Infrastructure.DjangoFramework.persistence.policies import can_user_propose_on
    
    can_access, _ = check_world_access(request, w_orm)
    can_propose = can_user_propose_on(request.user, w_orm)
    
    if not can_propose:
         messages.error(request, "⛔ No tienes permisos para editar este mundo.")
         return redirect('ver_mundo', public_id=w_orm.public_id if w_orm.public_id else w_orm.id)

    # is_admin_bypass logic (Superuser/Admin can edit Locked?)
    # Usually only World Owner or Superuser can edit LOCKED.
    # can_user_propose_on grants access to Collaborators too, but locked status overrides that.
    
    can_override_lock = request.user.is_superuser or w_orm.author == request.user
    
    is_admin_bypass = request.user.is_superuser
    try:
        if not is_admin_bypass and request.user.profile.rank == 'SUPERADMIN':
            is_admin_bypass = True
    except: pass
    
    if w_orm.status == 'LOCKED' and not can_override_lock:
        messages.error(request, "⛔ Este mundo está BLOQUEADO por el Autor. No se permiten propuestas.")
        return redirect('ver_mundo', public_id=w_orm.public_id if w_orm.public_id else w_orm.id)

    if request.method == 'POST':
        try:
            w = resolve_jid_orm(jid); real_jid = w.id if w else jid
            desc = request.POST.get('description')
            action_type = request.POST.get('action_type', 'EDIT_WORLD')
            
            metadata_prop = None
            reason = request.POST.get('reason', 'Actualización de Metadatos')
 
            # Manejar Propuesta de Metadatos
            if action_type == 'METADATA_PROPOSAL':
                # NUEVA LÓGICA DINÁMICA (Arrays)
                prop_keys = request.POST.getlist('prop_keys[]')
                prop_values = request.POST.getlist('prop_values[]')
                
                metadata_prop = {'properties': []}
                
                # Unirlos (zip)
                if prop_keys and prop_values:
                    for k, v in zip(prop_keys, prop_values):
                        if k.strip(): # Ignorar claves vacías
                            metadata_prop['properties'].append({'key': k.strip(), 'value': v.strip()})
                
                print(f"📝 [Edición Manual] Enviando Propuesta de Metadatos: {len(metadata_prop['properties'])} elementos.")
                print(f"   Contenido: {metadata_prop}")
                
                # Al editar metadatos, podríamos mantener nombre/desc como están (o usar campos ocultos)
                # Por seguridad, simplemente pasamos None para mantener los valores existentes en el Caso de Uso
                ProposeChangeUseCase().execute(real_jid, None, None, reason, get_current_user(request), metadata_proposal=metadata_prop)
                messages.success(request, f"🔮 Propuesta de METADATOS enviada (v{CaosVersionORM.objects.filter(world_id=real_jid).count() + 1}).")
                log_event(request.user, "PROPOSE_METADATA", real_jid, f"Razón: {reason}")
            else:
                # Edición Regular
                if request.POST.get('use_ai_edit') == 'on':
                    try: desc = Llama3Service().generate_description(f"Nombre: {request.POST.get('name')}. Concepto: {desc}") or desc
                    except: pass
                ProposeChangeUseCase().execute(real_jid, request.POST.get('name'), desc, request.POST.get('reason'), get_current_user(request))
                log_event(request.user, "PROPOSE_CHANGE", real_jid, f"Reason: {request.POST.get('reason')}")
            
            return redirect('ver_mundo', public_id=w.public_id if w.public_id else w.id)
        except Exception as e: 
            print(f"Error de edición: {e}")
            return redirect('home')
 
    # --- GET: RENDERIZAR FORMULARIO DE EDICIÓN ---
    from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
    try:
        # 1. Obtener Contexto Base
        repo = DjangoCaosRepository()
        use_case = GetWorldDetailsUseCase(repo)
        context = use_case.execute(real_jid, request.user)
        
        # 2. Activar Modo Edición
        context['edit_mode'] = True
        
        # 3. Aplicar Sobrescrituras de Retoque (lógica movida aquí por robustez)
        src_version_id = request.GET.get('src_version')
        if src_version_id:
            try:
                v_src = CaosVersionORM.objects.get(id=src_version_id)
                # Verificar propiedad/relación
                can_retouch = (v_src.author == request.user) or is_admin_bypass
                
                if v_src.world.id == real_jid and can_retouch:
                    context['name'] = v_src.proposed_name
                    context['description'] = v_src.proposed_description
                    context['is_retouch_mode'] = True
                    context['can_edit'] = True # Forzar visibilidad del botón Editar
                    messages.info(request, f"✏️ Retomando propuesta rechazada v{v_src.version_number}. Datos cargados.")
            except Exception as e:
                print(f"Error cargando src_version en GET: {e}")
 
        return render(request, 'ficha_mundo.html', context)
    except Exception as e:
        print(f"Error renderizando vista de edición: {e}")
        return redirect('home')
