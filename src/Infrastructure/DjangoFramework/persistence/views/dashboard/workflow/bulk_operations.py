"""
Operaciones masivas sobre propuestas.
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
from ..utils import log_event, is_admin_or_staff, has_authority_over_proposal, execute_use_case_action, execute_orm_status_change
from ..metrics import group_items_by_author, calculate_kpis
from src.Infrastructure.DjangoFramework.persistence.rbac import restrict_explorer, admin_only, requires_role


@login_required
def borrar_propuestas_masivo(request): 
    """
    Procesador de acciones masivas para el Dashboard (Pendientes).
    Maneja:
    - 'reject': Rechazo masivo.
    - 'restore': Restauración masiva (No común en dashboard, pero soportado).
    - 'archive': Archivado masivo.
    - 'hard_delete': Borrado físico masivo (Solo Superusuarios/Admins).
    """
    # MULTI-PURPOSE BULK ACTION (Reject, Restore, Hard Delete)
    if request.method == 'POST':
        action_type = request.POST.get('action_type', 'reject')
        w_ids = request.POST.getlist('selected_ids')
        n_ids = request.POST.getlist('selected_narr_ids')
        i_ids = request.POST.getlist('selected_img_ids')
        p_ids = request.POST.getlist('selected_period_ids')
        
        count = len(w_ids) + len(n_ids) + len(i_ids) + len(p_ids)
        
        if action_type == 'restore':
            for id in w_ids: execute_use_case_action(request, RestoreVersionUseCase, id, "", "")
            for id in n_ids: execute_use_case_action(request, RestoreNarrativeVersionUseCase, id, "", "")
            CaosImageProposalORM.objects.filter(id__in=i_ids).update(status='PENDING')
            messages.success(request, f"🔄 {count} Elementos restaurados a Pendientes.")
            
        elif action_type == 'archive':
            # Bulk Archive
            CaosNarrativeVersionORM.objects.filter(id__in=n_ids).update(status='ARCHIVED')
            CaosImageProposalORM.objects.filter(id__in=i_ids).update(status='ARCHIVED')
            TimelinePeriodVersion.objects.filter(id__in=p_ids).update(status='ARCHIVED')
            messages.success(request, f"📦 {count} Elementos movidos al Archivo.")

        elif action_type == 'hard_delete':
            # Hard Delete (Superuser + Admin)
            if request.user.is_staff or request.user.is_superuser:
                CaosVersionORM.objects.filter(id__in=w_ids).delete()
                CaosNarrativeVersionORM.objects.filter(id__in=n_ids).delete()
                CaosImageProposalORM.objects.filter(id__in=i_ids).delete()
                TimelinePeriodVersion.objects.filter(id__in=p_ids).delete()
                messages.success(request, f"💀 {count} Elementos eliminados definitivamente.")
            else:
                messages.error(request, "⛔ Solo Superusuarios o Admins pueden borrar definitivamente.")
                
        else: # Default: REJECT (Cancel)
            for id in w_ids: execute_use_case_action(request, RejectVersionUseCase, id, "", "")
            for id in n_ids: execute_use_case_action(request, RejectNarrativeVersionUseCase, id, "", "")
            CaosImageProposalORM.objects.filter(id__in=i_ids).update(status='REJECTED')
            messages.success(request, f"✕ {count} Elementos rechazados.")
 
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def aprobar_propuestas_masivo(request):
    if request.method == 'POST':
        w_ids = request.POST.getlist('selected_ids')
        n_ids = request.POST.getlist('selected_narr_ids')
        i_ids = request.POST.getlist('selected_img_ids')
        p_ids = request.POST.getlist('selected_period_ids')
        
        for id in w_ids: execute_use_case_action(request, ApproveVersionUseCase, id, "", "")
        for id in n_ids: execute_use_case_action(request, ApproveNarrativeVersionUseCase, id, "", "")
        
        for id in p_ids:
            try:
                obj = TimelinePeriodVersion.objects.get(id=id)
                TimelinePeriodService.approve_version(obj, request.user)
            except: pass
            
        if i_ids:
            from .assets import aprobar_imagen
            for iid in i_ids: aprobar_imagen(request, iid)
        
        total = len(w_ids) + len(n_ids) + len(i_ids) + len(p_ids)
        messages.success(request, f"✅ {total} Propuestas aprobadas.")
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def archivar_propuestas_masivo(request): 
    if request.method == 'POST':
        w_ids = request.POST.getlist('selected_ids')
        n_ids = request.POST.getlist('selected_narr_ids')
        i_ids = request.POST.getlist('selected_img_ids')
        p_ids = request.POST.getlist('selected_period_ids')
        
        count = 0
        for vid in w_ids:
            execute_orm_status_change(request, CaosVersionORM, vid, 'ARCHIVED', "", "")
            count += 1
        for nid in n_ids:
            execute_orm_status_change(request, CaosNarrativeVersionORM, nid, 'ARCHIVED', "", "")
            count += 1
        for iid in i_ids:
            execute_orm_status_change(request, CaosImageProposalORM, iid, 'ARCHIVED', "", "")
            count += 1
        for pid in p_ids:
            execute_orm_status_change(request, TimelinePeriodVersion, pid, 'ARCHIVED', "", "")
            count += 1
            
        if count > 0:
            messages.success(request, f"Box {count} Propuestas archivadas correctamente.")
            log_event(request.user, "BULK_ARCHIVE", f"Archivadas {count} propuestas mixtas.")
            
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def publicar_propuestas_masivo(request): 
    if request.method == 'POST':
        w_ids = request.POST.getlist('selected_ids')
        n_ids = request.POST.getlist('selected_narr_ids')
        i_ids = request.POST.getlist('selected_img_ids')
        
        count = 0
        for vid in w_ids:
            execute_use_case_action(request, PublishToLiveVersionUseCase, vid, "", "", extra_args={'user': request.user})
            count += 1
        for nid in n_ids:
            execute_use_case_action(request, PublishNarrativeToLiveUseCase, nid, "", "")
            count += 1
            
        if i_ids:
            from .assets import publicar_imagen
            for iid in i_ids:
                try:
                    publicar_imagen(request, iid)
                    count += 1
                except: pass
        
        # Periodos
        p_ids = request.POST.getlist('selected_period_ids')
        if p_ids:
            for pid in p_ids:
                try:
                    obj = TimelinePeriodVersion.objects.get(id=pid)
                    TimelinePeriodService.publish_version(obj, request.user)
                    count += 1
                except: pass
        
        if count > 0:
            messages.success(request, f"🚀 {count} Propuestas ejecutadas correctamente (Publicadas/Borradas).")
            log_event(request.user, "BULK_PUBLISH", f"Publicadas {count} propuestas mixtas.")
            
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')
