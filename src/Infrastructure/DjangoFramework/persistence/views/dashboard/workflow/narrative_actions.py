"""
Acciones sobre propuestas de narrativas.
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
def aprobar_narrativa(request, id):
    """
    Aprueba una propuesta de narrativa (CaosNarrativeVersionORM).
    Requiere ser Superusuario o el Autor del mundo asociado.
    """
    obj = get_object_or_404(CaosNarrativeVersionORM, id=id)
    if not has_authority_over_proposal(request.user, obj):
        messages.error(request, "⛔ Solo el Administrador de este mundo puede aprobar esta narrativa.")
        return redirect('dashboard')
    return execute_use_case_action(request, ApproveNarrativeVersionUseCase, id, "Narrativa aprobada.", "APPROVE_NARRATIVE")

@login_required
def rechazar_narrativa(request, id):
    """
    Rechaza una propuesta de narrativa con feedback opcional.
    """
    obj = get_object_or_404(CaosNarrativeVersionORM, id=id)
    if not has_authority_over_proposal(request.user, obj):
        messages.error(request, "⛔ Solo el Administrador de este mundo puede rechazar esta narrativa.")
        return redirect('dashboard')
    feedback = request.POST.get('admin_feedback', '') or request.GET.get('admin_feedback', '')
    return execute_use_case_action(request, RejectNarrativeVersionUseCase, id, "Narrativa rechazada.", "REJECT_NARRATIVE", extra_args={'reason': feedback})

@login_required
@admin_only
def publicar_narrativa(request, id):
    return execute_use_case_action(request, PublishNarrativeToLiveUseCase, id, "Narrativa LIVE.", "PUBLISH_NARRATIVE_LIVE")

@login_required
def archivar_narrativa(request, id):
    obj = get_object_or_404(CaosNarrativeVersionORM, id=id)
    from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
    check_ownership(request.user, obj)

    if obj.action == 'DELETE' and (request.user.is_staff or request.user.is_superuser) and obj.status == 'PENDING':
        feedback = request.POST.get('admin_feedback', '') or request.GET.get('admin_feedback', '')
        return execute_use_case_action(request, RejectNarrativeVersionUseCase, id, "Borrado de narrativa rechazado (Mantener).", "KEEP_NARRATIVE_REJECT_DELETE", extra_args={'reason': feedback or "El administrador ha decidido mantener esta narrativa."})

    return execute_orm_status_change(request, CaosNarrativeVersionORM, id, 'ARCHIVED', "Archivado.", "ARCHIVE_NARRATIVE")

@login_required
def restaurar_narrativa(request, id):
    obj = get_object_or_404(CaosNarrativeVersionORM, id=id)
    
    # NUEVA LÓGICA: Crear propuesta en lugar de restaurar estado
    new_v_num = CaosNarrativeVersionORM.objects.filter(narrative=obj.narrative).count() + 1
    new_proposal = CaosNarrativeVersionORM.objects.create(
        narrative=obj.narrative,
        proposed_title=obj.proposed_title,
        proposed_content=obj.proposed_content,
        version_number=new_v_num,
        status='PENDING',
        action='EDIT',
        change_log=f"Recuperar narrativa (v{obj.version_number})",
        author=request.user
    )
    messages.success(request, f"🔄 Propuesta de restauración creada (v{new_v_num}).")
    messages.success(request, f"🔄 Propuesta de restauración creada (v{new_v_num}).")
    
    if request.POST.get('action') == 'retouch':
        # Redirect to the viewer which handles src_version and opens the editor
        return redirect(f"/narrativa/{obj.narrative.public_id or obj.narrative.nid}/?src_version={obj.id}")
        
    return redirect('dashboard')

@login_required
def borrar_narrativa_version(request, id):
    obj = get_object_or_404(CaosNarrativeVersionORM, id=id)
    from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
    check_ownership(request.user, obj)
    return execute_orm_delete(request, CaosNarrativeVersionORM, id, "Versión eliminada.", "DELETE_NARRATIVE")
