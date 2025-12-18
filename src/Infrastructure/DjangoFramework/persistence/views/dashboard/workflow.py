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
    ContributionProposal
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
from .utils import log_event, is_admin_or_staff
from .metrics import group_items_by_author, calculate_kpis
from src.Infrastructure.DjangoFramework.persistence.rbac import restrict_explorer, admin_only, requires_role

@login_required
@restrict_explorer # Explorers cannot access Dashboard at all
def dashboard(request):
    # =========================================================================
    # JURISDICTION & ACCESS CONTROL
    # =========================================================================
    user = request.user
    allowed_authors = User.objects.all() # Trusted Mode

    # =========================================================================
    # GET PARAMETERS (FILTERS)
    # =========================================================================
    filter_author_id = request.GET.get('author')
    filter_type = request.GET.get('type')
    search_query = request.GET.get('q')

    # =========================================================================
    # BASE QUERYSETS
    # =========================================================================
    if request.user.is_superuser:
        w_qs = CaosVersionORM.objects.all().select_related('world', 'author')
        n_qs = CaosNarrativeVersionORM.objects.all().select_related('narrative__world', 'author')
        i_qs = CaosImageProposalORM.objects.all().select_related('world', 'author')
    else:
        # Hierarchy Filter
        my_bosses = []
        if hasattr(request.user, 'profile'):
            boss_profiles = request.user.profile.bosses.all()
            my_bosses = [bp.user for bp in boss_profiles if bp.user]
        visible_users = [request.user] + my_bosses
        q_filter = Q(author__in=visible_users)
        
        w_qs = CaosVersionORM.objects.filter(q_filter).select_related('world', 'author')
        i_qs = CaosImageProposalORM.objects.filter(q_filter).select_related('world', 'author')
        n_qs = CaosNarrativeVersionORM.objects.filter(q_filter).select_related('narrative__world', 'author')

    # =========================================================================
    # DYNAMIC FILTERS
    # =========================================================================
    if filter_author_id:
        try:
            current_target_author = int(filter_author_id)
            w_qs = w_qs.filter(author_id=current_target_author)
            n_qs = n_qs.filter(author_id=current_target_author)
            i_qs = i_qs.filter(author_id=current_target_author)
        except ValueError: pass

    if search_query:
        w_qs = w_qs.filter(Q(proposed_name__icontains=search_query) | Q(change_log__icontains=search_query))
        n_qs = n_qs.filter(Q(proposed_title__icontains=search_query) | Q(proposed_content__icontains=search_query))
        i_qs = i_qs.filter(title__icontains=search_query)

    if filter_type == 'WORLD':
        n_qs = n_qs.none(); i_qs = i_qs.none()
    elif filter_type == 'NARRATIVE':
        w_qs = w_qs.none(); i_qs = i_qs.none()
    elif filter_type == 'IMAGE':
        w_qs = w_qs.none(); n_qs = n_qs.none()

    # =========================================================================
    # SEGMENTATION
    # =========================================================================
    w_pending = list(w_qs.filter(status='PENDING').order_by('-created_at'))
    w_approved = list(w_qs.filter(status='APPROVED').order_by('-created_at'))
    w_rejected = list(w_qs.filter(status='REJECTED').order_by('-created_at')[:10])
    w_archived = list(w_qs.filter(status='ARCHIVED').order_by('-created_at')[:20])

    n_pending = list(n_qs.filter(status='PENDING').order_by('-created_at'))
    n_approved = list(n_qs.filter(status='APPROVED').order_by('-created_at'))
    n_rejected = list(n_qs.filter(status='REJECTED').order_by('-created_at')[:10])
    n_archived = list(n_qs.filter(status='ARCHIVED').order_by('-created_at')[:20])

    i_pending = list(i_qs.filter(status='PENDING').order_by('-created_at'))
    i_approved = list(i_qs.filter(status='APPROVED').order_by('-created_at'))
    i_rejected = list(i_qs.filter(status='REJECTED').order_by('-created_at')[:10])
    i_archived = list(i_qs.filter(status='ARCHIVED').exclude(action='DELETE').order_by('-created_at'))

    # TAG Items
    for x in w_pending + w_approved + w_rejected + w_archived:
        x.type = 'WORLD'
        x.type_label = '🌍 MUNDO'
        x.target_name = x.proposed_name
        x.target_desc = x.proposed_description
        x.parent_context = "Universo"
        if x.cambios.get('action') == 'SET_COVER':
            x.target_desc = f"📸 Cambio: {x.cambios.get('cover_image')}"
        elif x.cambios.get('action') == 'TOGGLE_VISIBILITY':
            x.target_desc = f"👁️ Visibilidad"
        x.target_link = x.world.public_id if x.world.public_id else x.world.id

    for x in n_pending + n_approved + n_rejected + n_archived:
        x.type = 'NARRATIVE'
        x.type_label = '📖 NARRATIVA'
        x.target_name = x.proposed_title
        x.target_desc = x.proposed_content
        x.target_link = x.narrative.public_id if hasattr(x.narrative, 'public_id') and x.narrative.public_id else x.narrative.nid
        x.parent_context = x.narrative.world.name

    for x in i_pending + i_approved + i_rejected + i_archived:
        x.type = 'IMAGE'
        x.type_label = '🖼️ IMAGEN'
        x.target_name = x.title or "(Sin Título)"
        x.target_desc = f"🗑️ Borrar: {x.target_filename}" if x.action == 'DELETE' else "📸 Nueva"
        if not hasattr(x, 'version_number'): x.version_number = 1 
        x.parent_context = x.world.name if x.world else "Global"
        x.change_log = x.target_desc

    pending = sorted(w_pending + n_pending + i_pending, key=lambda x: x.created_at, reverse=True)
    approved = sorted(w_approved + n_approved + i_approved, key=lambda x: x.created_at, reverse=True)
    rejected = sorted(w_rejected + n_rejected + i_rejected, key=lambda x: x.created_at, reverse=True)
    archived = sorted(w_archived + n_archived + i_archived, key=lambda x: x.created_at, reverse=True)

    logs_base = CaosEventLog.objects.all().order_by('-timestamp')[:50]
    logs_world = [l for l in logs_base if 'WORLD' in l.action.upper()]
    logs_narrative = [l for l in logs_base if 'NARRATIVE' in l.action.upper()]
    logs_image = [l for l in logs_base if 'IMAGE' in l.action.upper()]
    logs_other = [l for l in logs_base if l not in logs_world + logs_narrative + logs_image]

    grouped_inbox = group_items_by_author(pending)
    grouped_approved = group_items_by_author(approved)
    grouped_archived = group_items_by_author(archived)
    
    kpis = calculate_kpis(pending, logs_base)

    context = {
        'pending': pending, 'approved': approved, 'rejected': rejected, 'archived': archived,
        'grouped_inbox': grouped_inbox, 'grouped_approved': grouped_approved, 'grouped_archived': grouped_archived,
        'logs_world': logs_world, 'logs_narrative': logs_narrative, 'logs_image': logs_image, 'logs_other': logs_other,
        'total_pending_count': kpis['total_pending_count'], 'total_activity_count': kpis['total_activity_count'],
        'available_authors': allowed_authors, 'current_author': int(filter_author_id) if filter_author_id else None,
        'current_type': filter_type, 'search_query': search_query,
    }
    return render(request, 'dashboard.html', context)

def centro_control(request):
    return redirect('dashboard')

# --- ACTIONS ---

@login_required
@admin_only
def aprobar_propuesta(request, id):
    try:
        if request.method == 'POST':
            use_case = ApproveVersionUseCase(DjangoCaosRepository())
            use_case.execute(id, request.user)
            messages.success(request, "Propuesta aprobada.")
            log_event(request.user, "APPROVE_WORLD_VERSION", id)
    except Exception as e: messages.error(request, f"Error: {e}")
    return redirect('dashboard')

@login_required
@admin_only
def rechazar_propuesta(request, id):
    try:
        use_case = RejectVersionUseCase(DjangoCaosRepository())
        use_case.execute(id, request.user, reason="Rechazado Dashboard")
        messages.success(request, "Rechazada.")
        log_event(request.user, "REJECT_WORLD_VERSION", id)
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
@admin_only
def publicar_version(request, version_id):
    try:
        use_case = PublishToLiveVersionUseCase(DjangoCaosRepository())
        use_case.execute(version_id, request.user)
        messages.success(request, "¡LIVE!")
        log_event(request.user, "PUBLISH_WORLD_VERSION", version_id)
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
def archivar_propuesta(request, id):
    try:
        v = get_object_or_404(CaosVersionORM, id=id)
        v.status = 'ARCHIVED'; v.save()
        messages.success(request, "Archivado.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
def restaurar_version(request, version_id):
    try:
        use_case = RestoreVersionUseCase(DjangoCaosRepository())
        use_case.execute(version_id, request.user)
        messages.success(request, "Restaurado.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
def borrar_propuesta(request, version_id):
    try:
        v = get_object_or_404(CaosVersionORM, id=version_id)
        v.delete()
        messages.success(request, "Eliminado.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
@admin_only
def aprobar_narrativa(request, id):
    try:
        use_case = ApproveNarrativeVersionUseCase(DjangoCaosRepository())
        use_case.execute(id, request.user)
        messages.success(request, "Narrativa aprobada.")
        log_event(request.user, "APPROVE_NARRATIVE", id)
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
@admin_only
def rechazar_narrativa(request, id):
    try:
        use_case = RejectNarrativeVersionUseCase(DjangoCaosRepository())
        use_case.execute(id, request.user, "Rechazado")
        messages.success(request, "Narrativa rechazada.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
@admin_only
def publicar_narrativa(request, id):
    try:
        use_case = PublishNarrativeToLiveUseCase(DjangoCaosRepository())
        use_case.execute(id, request.user)
        messages.success(request, "Narrativa LIVE.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
def archivar_narrativa(request, id):
    try:
        n = get_object_or_404(CaosNarrativeVersionORM, id=id)
        n.status = 'ARCHIVED'; n.save()
        messages.success(request, "Archivado.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
def restaurar_narrativa(request, id):
    try:
        use_case = RestoreNarrativeVersionUseCase(DjangoCaosRepository())
        use_case.execute(id, request.user)
        messages.success(request, "Restaurada.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
def borrar_narrativa_version(request, id):
    try:
        v = get_object_or_404(CaosNarrativeVersionORM, id=id)
        v.delete()
        messages.success(request, "Versión eliminada.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

# Bulk Placeholders
@login_required
def borrar_propuestas_masivo(request): return redirect('dashboard')
@login_required
def aprobar_propuestas_masivo(request): return redirect('dashboard')
@login_required
def archivar_propuestas_masivo(request): return redirect('dashboard')
@login_required
def publicar_propuestas_masivo(request): return redirect('dashboard')

# --- TEXT PROPOSAL CONTRIBUTIONS ---

class ProposalDetailView(LoginRequiredMixin, View):
    def get(self, request, id):
        try:
            prop = ContributionProposal.objects.select_related('target_entity', 'proposer').get(id=id)
            context = {'prop': prop, 'target_entity': prop.target_entity}
            if prop.contribution_type == 'EDIT':
                context['diffs'] = DiffService.compare_entity(prop.target_entity, prop.proposed_payload)
            elif prop.contribution_type == 'CREATE':
                context['preview'] = DiffService.get_create_preview(prop.proposed_payload)
            return render(request, 'staff/proposal_detail.html', context)
        except ContributionProposal.DoesNotExist:
            return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def aprobar_contribucion(request, id):
    try:
        prop = ContributionProposal.objects.get(id=id)
        prop.status = 'APPROVED_WAITING'
        prop.reviewer = request.user
        prop.save()
        messages.success(request, "✅ Validado (Envíado a Staging).")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def rechazar_contribucion(request, id):
    try:
        prop = ContributionProposal.objects.get(id=id)
        prop.status = 'REJECTED'
        prop.reviewer = request.user
        prop.save()
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')
