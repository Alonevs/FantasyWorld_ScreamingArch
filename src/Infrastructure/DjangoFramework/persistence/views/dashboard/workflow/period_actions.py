"""
Acciones sobre períodos temporales.
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
from src.Shared.Services.TimelinePeriodService import TimelinePeriodService

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
def aprobar_periodo(request, id):
    try:
        if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rank in ['ADMIN', 'SUPERADMIN'])):
             messages.error(request, "⛔ No tienes permiso para aprobar periodos.")
             return redirect('dashboard')
        
        version = get_object_or_404(TimelinePeriodVersion, id=id)
        TimelinePeriodService.approve_version(version, request.user)
        messages.success(request, "Periodo aprobado.")
        log_event(request.user, "APPROVE_PERIOD", id)
    except Exception as e:
        messages.error(request, f"Error: {e}")
    
    return redirect('dashboard')

@login_required
def rechazar_periodo(request, id):
    try:
        if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rank in ['ADMIN', 'SUPERADMIN'])):
             messages.error(request, "⛔ No tienes permiso.")
             return redirect('dashboard')
             
        version = get_object_or_404(TimelinePeriodVersion, id=id)
        feedback = request.POST.get('admin_feedback', '') or request.GET.get('admin_feedback', '')
        TimelinePeriodService.reject_version(version, request.user, feedback)
        messages.success(request, "Periodo rechazado.")
        log_event(request.user, "REJECT_PERIOD", id)
    except Exception as e:
        messages.error(request, f"Error: {e}")
    
    return redirect('dashboard')

@login_required
def publicar_periodo(request, id):
    try:
        # Assuming ID refers to VERSION ID in dashboard context for publishing?
        # Or Period ID? 
        # In dashboard we see PROPOSALS (Versions).
        # But publish usually takes Live Object? 
        # Wait, usually we publish a VERSION to LIVE.
        # But TimelinePeriodService.publish_version takes 'version'.
        
        version = get_object_or_404(TimelinePeriodVersion, id=id)
        
        if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rank in ['ADMIN', 'SUPERADMIN'])):
             messages.error(request, "⛔ No tienes permiso.")
             return redirect('dashboard')

        TimelinePeriodService.publish_version(version, request.user)
        messages.success(request, "Periodo publicado a LIVE.")
        log_event(request.user, "PUBLISH_PERIOD", id)
    except Exception as e:
        messages.error(request, f"Error: {e}")
    
    return redirect('dashboard')

@login_required
def archivar_periodo(request, id):
    return execute_orm_status_change(request, TimelinePeriodVersion, id, 'ARCHIVED', "Periodo Archivado.", "ARCHIVE_PERIOD")

@login_required
def restaurar_periodo(request, id):
    # Retrieve object
    obj = get_object_or_404(TimelinePeriodVersion, id=id)
    
    # Check ownership
    # Owner or Superuser
    if not (request.user.is_superuser or obj.author == request.user or (obj.period and obj.period.world.author == request.user)):
        messages.error(request, "⛔ No tienes permiso.")
        return redirect('dashboard')

    # HANDLE RETOUCH REDIRECT (Pre-creation)
    if request.POST.get('action') == 'retouch':
        # Redirect to World Page with flag to open Period Edit Modal AND specific proposal ID to pre-fill
        # Using URL Construction to ensure parameters
        w = obj.period.world
        pid = w.public_id if w.public_id else w.id
        # We need period slug.
        return redirect(f"/mundo/{pid}/?period={obj.period.slug}&edit_period=true&proposal_id={obj.id}")

    # Logic: Create new pending version based on this one
    try:
        new_v = TimelinePeriodService.propose_edit(
            period=obj.period,
            title=obj.proposed_title,
            description=obj.proposed_description,
            metadata=obj.proposed_metadata,
            author=request.user,
            change_log=f"Restaurado desde v{obj.version_number}"
        )
        messages.success(request, f"🔄 Periodo restaurado (v{new_v.version_number}).")
    except Exception as e:
        messages.error(request, f"Error restaurando: {e}")

    return redirect('dashboard')

@login_required
def borrar_periodo(request, id):
    # This deletes the PROPOSAL (Version)
    return execute_orm_delete(request, TimelinePeriodVersion, id, "Propuesta de periodo eliminada.", "DELETE_PERIOD_VERSION")
