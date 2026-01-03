"""
Acciones sobre propuestas de mundos.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.views import View
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin

from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosVersionORM, CaosEventLog, CaosNarrativeVersionORM, 
    CaosImageProposalORM, CaosWorldORM, CaosNarrativeORM,
    ContributionProposal, TimelinePeriodVersion, TimelinePeriod
)
from django.contrib.auth.models import User
from src.Shared.Services.DiffService import DiffService

# Use Cases
from src.WorldManagement.Caos.Application.approve_version import ApproveVersionUseCase
from src.WorldManagement.Caos.Application.reject_version import RejectVersionUseCase
from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
from src.WorldManagement.Caos.Application.approve_narrative_version import ApproveNarrativeVersionUseCase
from src.WorldManagement.Caos.Application.reject_narrative_version import RejectNarrativeVersionUseCase
from src.WorldManagement.Caos.Application.publish_narrative_to_live import PublishNarrativeToLiveUseCase
from src.WorldManagement.Caos.Application.restore_narrative_version import RestoreNarrativeVersionUseCase
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository

# Modules
from ..utils import (
    log_event, is_admin_or_staff, has_authority_over_proposal,
    execute_use_case_action, execute_orm_status_change, execute_orm_delete
)
from ..metrics import group_items_by_author, calculate_kpis
from src.Infrastructure.DjangoFramework.persistence.rbac import restrict_explorer, admin_only, requires_role


@login_required
def aprobar_propuesta(request, id):
    """
    Aprueba una propuesta de cambio en un Mundo (CaosVersionORM).
    Solo el Superusuario o el Autor del mundo (Boss) tienen permiso.
    """
    obj = get_object_or_404(CaosVersionORM, id=id)
    if not has_authority_over_proposal(request.user, obj):
        messages.error(request, "⛔ Solo el Administrador de este mundo puede aprobar esta propuesta.")
        return redirect('dashboard')
    
    # Allow GET for redirects from Review System
    return execute_use_case_action(request, ApproveVersionUseCase, id, "Propuesta aprobada.", "APPROVE_WORLD_VERSION")

@login_required
def rechazar_propuesta(request, id):
    """
    Rechaza una propuesta de cambio en un Mundo.
    Permite adjuntar feedback administrativo para explicar la razón del rechazo.
    """
    obj = get_object_or_404(CaosVersionORM, id=id)
    if not has_authority_over_proposal(request.user, obj):
        messages.error(request, "⛔ Solo el Administrador de este mundo puede rechazar esta propuesta.")
        return redirect('dashboard')

    feedback = request.POST.get('admin_feedback', '') or request.GET.get('admin_feedback', '')
    return execute_use_case_action(request, RejectVersionUseCase, id, "Rechazada.", "REJECT_WORLD_VERSION", extra_args={'reason': feedback})

@login_required
def publicar_version(request, version_id):
    """
    Publica una versión aprobada al entorno LIVE (Producción).
    Actualiza los datos maestros del mundo y archiva la versión anterior.
    """
    return execute_use_case_action(request, PublishToLiveVersionUseCase, version_id, f"Versión {version_id} publicada LIVE.", "PUBLISH_LIVE")

@login_required
def archivar_propuesta(request, id):
    """
    Mueve una propuesta al archivo sin aprobarla ni rechazarla explícitamente (Soft Archive).
    Si la propuesta era de tipo DELETE y la acción es ejecutada por un Admin, se interpreta como un rechazo al borrado (Mantener entidad).
    """
    obj = get_object_or_404(CaosVersionORM, id=id)
    # check_ownership removed to allow World Owner/Admin actions via has_authority_over_proposal
    
    # If it's a DELETE proposal and coming from Admin ('archivar' is 'Mantener' in UI)
    is_delete = obj.cambios.get('action') == 'DELETE' if obj.cambios else False
    
    # FIX: Solo aplicar lógica de "Mantener" (Rechazar borrado) si está PENDING.
    # Si ya fue rechazada, solo la movemos al archivo.
    if is_delete and (request.user.is_staff or request.user.is_superuser) and obj.status == 'PENDING':
        feedback = request.POST.get('admin_feedback', '') or request.GET.get('admin_feedback', '')
        return execute_use_case_action(request, RejectVersionUseCase, id, "Propuesta de borrado rechazada (Mantenido).", "KEEP_WORLD_REJECT_DELETE", extra_args={'reason': feedback or "El administrador ha decidido mantener este elemento."})

    return execute_orm_status_change(request, CaosVersionORM, id, 'ARCHIVED', "Archivado.", "ARCHIVE_VERSION")

@login_required
def restaurar_version(request, version_id):
    """
    Restaura una versión desde el Archivo/Rechazados a estado PENDING.
    Permite reiniciar el ciclo de revisión de una propuesta descartada anteriormente.
    """
    obj = get_object_or_404(CaosVersionORM, id=version_id)
    # check_ownership removed to allow World Owner/Admin actions via has_authority_over_proposal
    
    # HANDLE RETOUCH REDIRECT (Pre-creation)
    # Si es 'retouch', NO restauramos automáticamente. 
    # Redirigimos al editor cargando los datos de la versión rechazada como 'source'.
    if request.POST.get('action') == 'retouch':
        target_id = obj.world.public_id if obj.world.public_id else obj.world.id
        
        # Detect if it's a metadata-only retouch (Auto-Noos wheel)
        is_meta = obj.cambios.get('action') == 'METADATA_UPDATE'
        if not is_meta:
             # Fallback check: if name and description didn't change but metadata did
             name_match = (obj.proposed_name == obj.world.name)
             desc_match = (obj.proposed_description == obj.world.description)
             has_meta = 'metadata' in obj.cambios or 'properties' in obj.cambios
             if name_match and desc_match and has_meta:
                 is_meta = True

        if is_meta:
            return redirect(f"/mundo/{target_id}/?edit_metadata=true&proposal_id={obj.id}")

        # Standard world retouch (text editor)
        return redirect(f"/editar/{target_id}/?src_version={obj.id}")
    
    # EXECUTE RESTORE (Standard)
    # Check permissions manually: Author OR Has Authority
    if not (request.user == obj.author or has_authority_over_proposal(request.user, obj)):
         messages.error(request, "⛔ No tienes permiso para restaurar esta versión.")
         return redirect('dashboard')

    # Crea una copia exacta en PENDING
    new_version_or_result = execute_use_case_action(request, RestoreVersionUseCase, version_id, "Restaurado.", "RESTORE_VERSION", skip_auth=True)
        
    return new_version_or_result

@login_required
def borrar_propuesta(request, version_id):
    """
    Elimina físicamente el registro de una propuesta (Hard Delete).
    Solo permitido para el propio Autor de la propuesta o un Administrador con permisos elevados.
    """
    # Borrado suave si es archivado, o eliminación total del registro de propuesta/archivada
    obj = get_object_or_404(CaosVersionORM, id=version_id)
    
    # Permisos: El autor de la propuesta o un Admin
    from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
    # Si no es admin, check_ownership lanzará excepción
    try:
        check_ownership(request.user, obj)
    except:
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "⛔ No tienes permiso para borrar esta propuesta.")
            return redirect('dashboard')

    return execute_orm_delete(request, CaosVersionORM, version_id, "Eliminado.", "DELETE_VERSION")
