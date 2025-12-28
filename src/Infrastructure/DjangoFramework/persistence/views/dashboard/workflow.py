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
    """
    Vista principal del Panel de Control (Dashboard).
    Centraliza las propuestas pendientes de Mundos, Narrativas e Imágenes.
    Aplica filtros de visibilidad basados en jerarquía (Jefe/Subordinado) y permite búsqueda y filtrado por autor.
    """
    # =========================================================================
    # JURISDICTION & ACCESS CONTROL
    # =========================================================================
    # =========================================================================
    # BASE QUERYSETS & VISIBILITY SCOPE
    # =========================================================================
    allowed_authors = []
    
    # =========================================================================
    # GET PARAMETERS (FILTERS)
    # =========================================================================
    filter_author_id = request.GET.get('author')
    filter_type = request.GET.get('type')
    search_query = request.GET.get('q')

    is_global_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rank == 'SUPERADMIN')

    if is_global_admin:
        w_qs = CaosVersionORM.objects.all().select_related('world', 'author')
        n_qs = CaosNarrativeVersionORM.objects.all().select_related('narrative__world', 'author')
        i_qs = CaosImageProposalORM.objects.all().select_related('world', 'author')
        allowed_authors = User.objects.filter(is_active=True).order_by('username')
    else:
        # TERRITORIAL SILO LOGIC:
        # Admins see:
        # 1. Their own proposals (always)
        # 2. Their Minions' proposals ONLY if targeting Admin's territory or shared worlds
        # 3. NOT Minions' proposals on System/Superuser worlds (those are private to Superuser)
        
        visible_ids = [request.user.id]
        minion_ids = []
        
        if hasattr(request.user, 'profile'):
            # Get my collaborators (Minions)
            minion_ids = list(request.user.profile.collaborators.values_list('user__id', flat=True))
            visible_ids.extend(minion_ids)
        
        # Base filter: Author must be me or my minion
        author_filter = Q(author_id__in=visible_ids)
        
        # TERRITORIAL RESTRICTION for Minions' proposals:
        # If proposal author is a Minion (not me), also check world ownership
        if minion_ids:
            # My proposals: no restriction
            my_proposals = Q(author_id=request.user.id)
            
            # Minions' proposals: ONLY if world.author is me or another minion (NOT Superuser/System)
            minion_proposals = Q(author_id__in=minion_ids) & (
                Q(world__author=request.user) |  # Targeting MY worlds
                Q(world__author_id__in=minion_ids)  # Or other minions' worlds (shared team)
            )
            
            territorial_filter = my_proposals | minion_proposals
        else:
            # No minions, just my own stuff
            territorial_filter = author_filter
        
        w_qs = CaosVersionORM.objects.filter(territorial_filter).select_related('world', 'author')
        i_qs = CaosImageProposalORM.objects.filter(territorial_filter).select_related('world', 'author')
        
        # Narratives need special handling (world is nested)
        if minion_ids:
            my_narr = Q(author_id=request.user.id)
            minion_narr = Q(author_id__in=minion_ids) & (
                Q(narrative__world__author=request.user) |
                Q(narrative__world__author_id__in=minion_ids)
            )
            n_territorial = my_narr | minion_narr
        else:
            n_territorial = Q(author_id=request.user.id)
            
        n_qs = CaosNarrativeVersionORM.objects.filter(n_territorial).select_related('narrative__world', 'author')
        
        # Restrict Filter Dropdown to only visible people
        allowed_authors = User.objects.filter(id__in=visible_ids).order_by('username')

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
        # Exclude SET_COVER from main world list as it's image-related
        w_qs = w_qs.exclude(cambios__action='SET_COVER')
        n_qs = n_qs.none(); i_qs = i_qs.none()
    elif filter_type == 'NARRATIVE':
        w_qs = w_qs.none(); i_qs = i_qs.none()
    elif filter_type == 'IMAGE':
        # Include normal image proposals PLUS SET_COVER actions from worlds
        w_qs = w_qs.filter(cambios__action='SET_COVER')
        n_qs = n_qs.none()
    elif filter_type == 'METADATA':
        w_qs = w_qs.filter(cambios__action='METADATA_UPDATE')
        n_qs = n_qs.none(); i_qs = i_qs.none()

    # =========================================================================
    # SEGMENTATION
    # =========================================================================
    # PENDIENTES: Propuestas nuevas esperando validación
    w_pending = list(w_qs.filter(status='PENDING').order_by('-created_at'))
    n_pending = list(n_qs.filter(status='PENDING').order_by('-created_at'))
    i_pending = list(i_qs.filter(status='PENDING').order_by('-created_at'))

    # APROBADAS: Validadas por admin, listas para publicar a LIVE
    w_approved = list(w_qs.filter(status='APPROVED').order_by('-created_at'))
    n_approved = list(n_qs.filter(status='APPROVED').order_by('-created_at'))
    i_approved = list(i_qs.filter(status='APPROVED').order_by('-created_at'))

    # RECHAZADAS: Propuestas descartadas (Historial de negatividad)
    w_rejected = list(w_qs.filter(status='REJECTED').order_by('-created_at')[:20])
    n_rejected = list(n_qs.filter(status='REJECTED').order_by('-created_at')[:20])
    i_rejected = list(i_qs.filter(status='REJECTED').order_by('-created_at')[:20])

    # TAG Items
    for x in w_pending + w_approved + w_rejected:
        x.type = 'WORLD'
        x.type_label = '🌍 MUNDO'
        x.target_name = x.proposed_name
        x.target_desc = x.proposed_description
        x.parent_context = "Universo"
        x.feedback = getattr(x, 'admin_feedback', '') # Ensure mapped
        if x.cambios.get('action') == 'SET_COVER':
            x.type_label = '🖼️ PORTADA'
            x.is_image_context = True
            x.target_desc = f"📸 Nueva Portada: {x.cambios.get('cover_image')}"
        elif x.cambios.get('action') == 'TOGGLE_VISIBILITY':
            x.target_desc = f"👁️ Visibilidad"
        elif x.cambios.get('action') == 'METADATA_UPDATE' or 'metadata' in x.cambios.keys():
            x.type = 'METADATA'
            x.type_label = '🧬 METADATOS'
            count = len(x.cambios.get('metadata', {}).get('properties', []))
            x.target_desc = f"🧬 Cambio en {count} variables"
        
        # Detect Deletion
        if (x.change_log and ("Eliminación" in x.change_log or "Borrar" in x.change_log)) or \
           (x.cambios and x.cambios.get('action') == 'DELETE'):
            x.action = 'DELETE'
            
        x.target_link = x.world.public_id if x.world.public_id else x.world.id

    for x in n_pending + n_approved + n_rejected:
        x.type = 'NARRATIVE'
        x.type_label = '📖 NARRATIVA'
        x.target_name = x.proposed_title
        x.target_desc = x.proposed_content
        x.target_link = x.narrative.public_id if hasattr(x.narrative, 'public_id') and x.narrative.public_id else x.narrative.nid
        x.parent_context = x.narrative.world.name
        x.feedback = getattr(x, 'admin_feedback', '') # Ensure mapped
        
        if (x.change_log and ("Eliminación" in x.change_log or "Borrar" in x.change_log)) or \
           (hasattr(x, 'cambios') and x.cambios and x.cambios.get('action') == 'DELETE'):
             x.action = 'DELETE'

    for x in i_pending + i_approved + i_rejected:
        x.type = 'IMAGE'
        x.type_label = '🖼️ IMAGEN'
        x.target_name = x.title or "(Sin Título)"
        x.feedback = getattr(x, 'admin_feedback', '') # Ensure mapped
        desc = f"🗑️ Borrar: {x.target_filename}" if x.action == 'DELETE' else "📸 Nueva"
        if hasattr(x, 'reason') and x.reason:
            desc = f"{desc} | Motivo: {x.reason}"
        x.target_desc = desc
        if not hasattr(x, 'version_number'): x.version_number = 1 
        x.parent_context = x.world.name if x.world else "Global"
        x.change_log = x.target_desc
        if "Borrar" in x.change_log: x.action = 'DELETE'

    pending = sorted(w_pending + n_pending + i_pending, key=lambda x: x.created_at, reverse=True)
    approved = sorted(w_approved + n_approved + i_approved, key=lambda x: x.created_at, reverse=True)
    rejected = sorted(w_rejected + n_rejected + i_rejected, key=lambda x: x.created_at, reverse=True)

    logs_base = CaosEventLog.objects.all().order_by('-timestamp')[:50]
    logs_world = [l for l in logs_base if 'WORLD' in l.action.upper()]
    logs_narrative = [l for l in logs_base if 'NARRATIVE' in l.action.upper()]
    logs_image = [l for l in logs_base if 'IMAGE' in l.action.upper()]
    logs_other = [l for l in logs_base if l not in logs_world + logs_narrative + logs_image]

    grouped_inbox = group_items_by_author(pending)
    grouped_approved = group_items_by_author(approved)
    grouped_rejected = group_items_by_author(rejected)
    
    # --- ENHANCE AVAILABLE AUTHORS WITH COUNTS ---
    # We do this for the dropdown to show who has pending stuff.
    for author in allowed_authors:
        w_p = CaosVersionORM.objects.filter(author_id=author.id, status='PENDING').count()
        n_p = CaosNarrativeVersionORM.objects.filter(author_id=author.id, status='PENDING').count()
        i_p = CaosImageProposalORM.objects.filter(author_id=author.id, status='PENDING').count()
        author.pending_count = w_p + n_p + i_p

    kpis = calculate_kpis(pending, logs_base)

    # =========================================================================
    # MY PERSONAL HISTORY (For "My Proposals" Tab)
    # =========================================================================
    # Independent of hierarchy, show ME my own past interactions.
    my_w = list(CaosVersionORM.objects.filter(author=request.user).exclude(status='PENDING').select_related('world').order_by('-created_at')[:30])
    my_n = list(CaosNarrativeVersionORM.objects.filter(author=request.user).exclude(status='PENDING').select_related('narrative__world').order_by('-created_at')[:30])
    my_i = list(CaosImageProposalORM.objects.filter(author=request.user).exclude(status='PENDING').select_related('world').order_by('-created_at')[:30])

    # Tag My Items
    for x in my_w:
        x.type = 'WORLD'
        x.type_label = '🌍 MUNDO'
        
        if x.cambios and x.cambios.get('action') == 'SET_COVER':
            x.type_label = '🖼️ PORTADA'
            x.is_image_context = True
            x.target_desc = f"📸 Portada: {x.cambios.get('cover_image')}"
        else:
            x.target_desc = x.proposed_description

        x.target_name = x.proposed_name
        x.target_link = x.world.public_id if x.world.public_id else x.world.id
    
    for x in my_n:
        x.type = 'NARRATIVE'
        x.type_label = '📖 NARRATIVA'
        x.target_name = x.proposed_title
        x.target_desc = x.proposed_content
        x.target_link = x.narrative.public_id if hasattr(x.narrative, 'public_id') and x.narrative.public_id else x.narrative.nid
    
    for x in my_i:
        x.type = 'IMAGE'
        x.type_label = '🖼️ IMAGEN'
        x.target_name = x.title or "Imagen"
        x.target_desc = x.reason or "Sin descripción"
        x.target_link = "#" # Images don't link well if deleted/archived

    my_history = sorted(my_w + my_n + my_i, key=lambda x: x.created_at, reverse=True)
    
    # Group by TYPE for organized display (instead of status)
    my_worlds = [x for x in my_history if x.type == 'WORLD']
    my_narratives = [x for x in my_history if x.type == 'NARRATIVE']
    my_images = [x for x in my_history if x.type == 'IMAGE']
    my_metadata = [x for x in my_history if x.type == 'METADATA']

    # PERMISSIONS FOR UI
    is_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rank in ['ADMIN', 'SUPERADMIN'])
    is_viewing_self = (int(filter_author_id) == request.user.id) if filter_author_id and filter_author_id.isdigit() else False
    
    # Can Bulk Approve? 
    # Must be Admin. 
    # If viewing SELF inbox, cannot approve (unless Superuser).
    can_bulk_approve = is_admin
    if is_viewing_self and not request.user.is_superuser:
        can_bulk_approve = False

    context = {
        'pending': pending, 'approved': approved, 'rejected': rejected,
        'grouped_inbox': grouped_inbox, 'grouped_approved': grouped_approved, 
        'grouped_rejected': grouped_rejected,
        'my_history': my_history,
        'my_worlds': my_worlds, 'my_narratives': my_narratives, 
        'my_images': my_images, 'my_metadata': my_metadata,
        'can_bulk_approve': can_bulk_approve, # NEW FLAG for UI
        'logs_world': logs_world, 'logs_narrative': logs_narrative, 'logs_image': logs_image, 'logs_other': logs_other,
        'total_pending_count': kpis['total_pending_count'], 'total_activity_count': kpis['total_activity_count'],
        'available_authors': allowed_authors, 'current_author': int(filter_author_id) if filter_author_id else None,
        'current_type': filter_type, 'search_query': search_query,
    }
    return render(request, 'dashboard.html', context)

def centro_control(request):
    return redirect('dashboard')

# --- ACTIONS (Refactored) ---
from .utils import execute_use_case_action, execute_orm_status_change, execute_orm_delete

# --- WORLD ACTIONS ---
@login_required
def aprobar_propuesta(request, id):
    """
    Aprueba una propuesta de cambio en un Mundo (CaosVersionORM).
    Solo el Superusuario o el Autor del mundo (Boss) tienen permiso.
    """
    # Verificación de Autoridad BOSS
    obj = get_object_or_404(CaosVersionORM, id=id)
    # RBAC Relax: Superusers can approve anything.
    if not request.user.is_superuser:
        # Original check for non-superusers
        if obj.world.author != request.user:
            messages.error(request, "⛔ Solo el Autor (Administrador) de este mundo puede aprobar esta propuesta.")
            return redirect('dashboard')
    
    # Allow GET for redirects from Review System
    return execute_use_case_action(request, ApproveVersionUseCase, id, "Propuesta aprobada.", "APPROVE_WORLD_VERSION")

@login_required
def rechazar_propuesta(request, id):
    """
    Rechaza una propuesta de cambio en un Mundo.
    Permite adjuntar feedback administrativo para explicar la razón del rechazo.
    """
    # Verificación de Autoridad BOSS
    obj = get_object_or_404(CaosVersionORM, id=id)
    if not (request.user.is_superuser or obj.world.author == request.user):
        messages.error(request, "⛔ Solo el Autor (Administrador) de este mundo puede rechazar esta propuesta.")
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
    from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
    check_ownership(request.user, obj)
    
    # If it's a DELETE proposal and coming from Admin ('archivar' is 'Mantener' in UI)
    is_delete = obj.cambios.get('action') == 'DELETE' if obj.cambios else False
    if is_delete and (request.user.is_staff or request.user.is_superuser):
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
    from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
    check_ownership(request.user, obj)
    return execute_use_case_action(request, RestoreVersionUseCase, version_id, "Restaurado.", "RESTORE_VERSION")

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

# --- NARRATIVE ACTIONS ---

@login_required
def aprobar_narrativa(request, id):
    """
    Aprueba una propuesta de narrativa (CaosNarrativeVersionORM).
    Requiere ser Superusuario o el Autor del mundo asociado.
    """
    obj = get_object_or_404(CaosNarrativeVersionORM, id=id)
    if not (request.user.is_superuser or obj.narrative.world.author == request.user):
        messages.error(request, "⛔ Solo el Autor (Administrador) de este mundo puede aprobar esta narrativa.")
        return redirect('dashboard')
    return execute_use_case_action(request, ApproveNarrativeVersionUseCase, id, "Narrativa aprobada.", "APPROVE_NARRATIVE")

@login_required
def rechazar_narrativa(request, id):
    """
    Rechaza una propuesta de narrativa con feedback opcional.
    """
    obj = get_object_or_404(CaosNarrativeVersionORM, id=id)
    if not (request.user.is_superuser or obj.narrative.world.author == request.user):
        messages.error(request, "⛔ Solo el Autor (Administrador) de este mundo puede rechazar esta narrativa.")
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

    if obj.action == 'DELETE' and (request.user.is_staff or request.user.is_superuser):
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
    return redirect('dashboard')

@login_required
def borrar_narrativa_version(request, id):
    obj = get_object_or_404(CaosNarrativeVersionORM, id=id)
    from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
    check_ownership(request.user, obj)
    return execute_orm_delete(request, CaosNarrativeVersionORM, id, "Versión eliminada.", "DELETE_NARRATIVE")

# Bulk Logic
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
        
        count = len(w_ids) + len(n_ids) + len(i_ids)
        
        if action_type == 'restore':
            for id in w_ids: execute_use_case_action(request, RestoreVersionUseCase, id, "", "")
            for id in n_ids: execute_use_case_action(request, RestoreNarrativeVersionUseCase, id, "", "")
            CaosImageProposalORM.objects.filter(id__in=i_ids).update(status='PENDING')
            messages.success(request, f"🔄 {count} Elementos restaurados a Pendientes.")
            
        elif action_type == 'archive':
            # Bulk Archive
            CaosVersionORM.objects.filter(id__in=w_ids).update(status='ARCHIVED')
            CaosNarrativeVersionORM.objects.filter(id__in=n_ids).update(status='ARCHIVED')
            CaosImageProposalORM.objects.filter(id__in=i_ids).update(status='ARCHIVED')
            messages.success(request, f"📦 {count} Elementos movidos al Archivo.")

        elif action_type == 'hard_delete':
            # Hard Delete (Superuser + Admin)
            if request.user.is_superuser or request.user.profile.rank == 'ADMIN':
                CaosVersionORM.objects.filter(id__in=w_ids).delete()
                CaosNarrativeVersionORM.objects.filter(id__in=n_ids).delete()
                CaosImageProposalORM.objects.filter(id__in=i_ids).delete()
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
        
        for id in w_ids: execute_use_case_action(request, ApproveVersionUseCase, id, "", "")
        for id in n_ids: execute_use_case_action(request, ApproveNarrativeVersionUseCase, id, "", "")
        
        if i_ids:
            from .assets import aprobar_imagen
            for iid in i_ids: aprobar_imagen(request, iid)
        
        total = len(w_ids) + len(n_ids) + len(i_ids)
        messages.success(request, f"✅ {total} Propuestas aprobadas.")
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def archivar_propuestas_masivo(request): 
    if request.method == 'POST':
        w_ids = request.POST.getlist('selected_ids')
        n_ids = request.POST.getlist('selected_narr_ids')
        i_ids = request.POST.getlist('selected_img_ids')
        
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
        
        if count > 0:
            messages.success(request, f"🚀 {count} Propuestas ejecutadas correctamente (Publicadas/Borradas).")
            log_event(request.user, "BULK_PUBLISH", f"Publicadas {count} propuestas mixtas.")
            
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')

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
