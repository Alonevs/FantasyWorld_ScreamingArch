"""
Vista principal del dashboard de workflow.
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
from ..utils import log_event, is_admin_or_staff, has_authority_over_proposal
from ..metrics import group_items_by_author, calculate_kpis
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
        p_qs = TimelinePeriodVersion.objects.all().select_related('period__world', 'author')
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
            territorial_filter = author_filter | Q(world__author=request.user)
        
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
            n_territorial = Q(author_id=request.user.id) | Q(narrative__world__author=request.user)
            
        n_qs = CaosNarrativeVersionORM.objects.filter(n_territorial).select_related('narrative__world', 'author')
        
        # Period status filtering (Territorial)
        if minion_ids:
            my_p = Q(author_id=request.user.id)
            minion_p = Q(author_id__in=minion_ids) & (
                Q(period__world__author=request.user) |
                Q(period__world__author_id__in=minion_ids)
            )
            p_territorial = my_p | minion_p
        else:
            p_territorial = Q(author_id=request.user.id) | Q(period__world__author=request.user)
        
        p_qs = TimelinePeriodVersion.objects.filter(p_territorial).select_related('period__world', 'author')
        
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
            p_qs = p_qs.filter(author_id=current_target_author)
        except ValueError: pass

    if search_query:
        w_qs = w_qs.filter(Q(proposed_name__icontains=search_query) | Q(change_log__icontains=search_query))
        n_qs = n_qs.filter(Q(proposed_title__icontains=search_query) | Q(proposed_content__icontains=search_query))
        i_qs = i_qs.filter(title__icontains=search_query)
        p_qs = p_qs.filter(Q(proposed_title__icontains=search_query) | Q(proposed_description__icontains=search_query))

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
    elif filter_type == 'PERIOD':
        w_qs = w_qs.none(); n_qs = n_qs.none(); i_qs = i_qs.none()
    elif filter_type == 'METADATA':
        w_qs = w_qs.filter(cambios__action='METADATA_UPDATE')
        n_qs = n_qs.none(); i_qs = i_qs.none(); p_qs = p_qs.none()

    # =========================================================================
    # SEGMENTATION
    # =========================================================================
    # PENDIENTES: Propuestas nuevas esperando validación
    w_pending = list(w_qs.filter(status='PENDING', change_type='LIVE').order_by('-created_at'))
    n_pending = list(n_qs.filter(status='PENDING').order_by('-created_at'))
    i_pending = list(i_qs.filter(status='PENDING').order_by('-created_at'))
    p_pending = list(p_qs.filter(status='PENDING').order_by('-created_at'))

    # APROBADAS: Validadas por admin, listas para publicar a LIVE
    w_approved = list(w_qs.filter(status='APPROVED', change_type='LIVE').order_by('-created_at'))
    n_approved = list(n_qs.filter(status='APPROVED').order_by('-created_at'))
    i_approved = list(i_qs.filter(status='APPROVED').order_by('-created_at'))
    p_approved = list(p_qs.filter(status='APPROVED').order_by('-created_at'))

    # RECHAZADAS: Propuestas descartadas (Historial de negatividad)
    w_rejected = list(w_qs.filter(status='REJECTED', change_type='LIVE').order_by('-created_at')[:20])
    n_rejected = list(n_qs.filter(status='REJECTED').order_by('-created_at')[:20])
    i_rejected = list(i_qs.filter(status='REJECTED').order_by('-created_at')[:20])
    p_rejected = list(p_qs.filter(status='REJECTED').order_by('-created_at')[:20])
    
    # TIMELINE: Propuestas de snapshots temporales
    timeline_pending = list(w_qs.filter(status='PENDING', change_type='TIMELINE').order_by('-created_at'))
    timeline_approved = list(w_qs.filter(status='APPROVED', change_type='TIMELINE').order_by('-created_at'))
    timeline_rejected = list(w_qs.filter(status='REJECTED', change_type='TIMELINE').order_by('-created_at')[:20])

    # TAG Items
    for x in w_pending + w_approved + w_rejected:
        context_str = " (Actual)" if x.change_type == 'LIVE' else f" (Año {x.timeline_year})"
        x.type = 'WORLD'
        x.type_label = f'🌍 MUNDO{context_str}'
        x.target_name = x.proposed_name
        x.target_desc = x.proposed_description
        x.parent_context = "Universo"
        x.feedback = getattr(x, 'admin_feedback', '') 
        if x.cambios.get('action') == 'SET_COVER':
            x.type_label = f'🖼️ PORTADA{context_str}'
            x.is_image_context = True
            x.target_desc = f"📸 Nueva Portada: {x.cambios.get('cover_image')}"
        elif x.cambios.get('action') == 'TOGGLE_VISIBILITY':
            x.target_desc = f"👁️ Visibilidad"
        elif x.cambios.get('action') == 'METADATA_UPDATE' or 'metadata' in x.cambios.keys():
            x.type = 'METADATA'
            x.type_label = f'🧬 METADATOS{context_str}'
            count = len(x.cambios.get('metadata', {}).get('properties', []))
            x.target_desc = f"🧬 Cambio en {count} variables"
        
        # Detect Deletion
        if (x.change_log and ("Eliminación" in x.change_log or "Borrar" in x.change_log)) or \
           (x.cambios and x.cambios.get('action') == 'DELETE'):
            x.action = 'DELETE'
            
        x.target_link = x.world.public_id if x.world.public_id else x.world.id

    for x in n_pending + n_approved + n_rejected:
        context_str = f" ({x.narrative.timeline_period.title})" if x.narrative.timeline_period else " (Actual)"
        x.type = 'NARRATIVE'
        x.type_label = f'📖 NARRATIVA{context_str}'
        x.target_name = x.proposed_title
        x.target_desc = x.proposed_content
        x.target_link = x.narrative.public_id if hasattr(x.narrative, 'public_id') and x.narrative.public_id else x.narrative.nid
        x.parent_context = f"{x.narrative.world.name}{context_str}"
        x.feedback = getattr(x, 'admin_feedback', '') 
        
        if (x.change_log and ("Eliminación" in x.change_log or "Borrar" in x.change_log)) or \
           (hasattr(x, 'cambios') and x.cambios and x.cambios.get('action') == 'DELETE'):
             x.action = 'DELETE'

    for x in i_pending + i_approved + i_rejected:
        context_str = f" ({x.timeline_period.title})" if x.timeline_period else " (Actual)"
        x.type = 'IMAGE'
        x.type_label = f'🖼️ IMAGEN{context_str}'
        x.target_name = x.title or "(Sin Título)"
        x.feedback = getattr(x, 'admin_feedback', '') 
        desc = f"🗑️ Borrar: {x.target_filename}" if x.action == 'DELETE' else "📸 Nueva"
        if hasattr(x, 'reason') and x.reason:
            desc = f"{desc} | Motivo: {x.reason}"
        x.target_desc = desc
        if not hasattr(x, 'version_number'): x.version_number = 1 
        x.parent_context = f"{x.world.name}{context_str}" if x.world else f"Global{context_str}"
        x.change_log = x.target_desc
        if "Borrar" in x.change_log: x.action = 'DELETE'

    for x in p_pending + p_approved + p_rejected:
        x.type = 'PERIOD'
        x.type_label = f'📅 PERIODO ({x.period.title})'
        x.target_name = x.proposed_title
        x.target_desc = x.proposed_description[:100] + '...' if x.proposed_description else "Sin descripción"
        x.target_link = f"{x.period.world.public_id}?period={x.period.slug}"
        x.parent_context = x.period.world.name
        x.feedback = getattr(x, 'admin_feedback', '')
        
        # Map actions correctly for UI
        if x.action == 'DELETE':
            x.target_desc = f"🗑️ Borrar Periodo: {x.period.title}"
        elif x.action == 'ADD':
            x.type_label = f'✨ NUEVO PERIODO ({x.period.title})'
    
    # TAG Timeline Items
    for x in timeline_pending + timeline_approved + timeline_rejected:
        x.type = 'TIMELINE'
        x.type_label = '📅 TIMELINE'
        x.target_name = x.world.name if x.world else "(Sin Mundo)"
        # Extract description from proposed_snapshot
        if x.proposed_snapshot and 'description' in x.proposed_snapshot:
            x.target_desc = x.proposed_snapshot['description'][:100] + '...'
        else:
            x.target_desc = "Snapshot temporal"
        x.parent_context = f"Año {x.timeline_year}" if x.timeline_year else "Sin año"
        x.feedback = getattr(x, 'admin_feedback', '')
        x.target_link = x.world.public_id if x.world and x.world.public_id else (x.world.id if x.world else None)

    pending = sorted(w_pending + n_pending + i_pending + p_pending, key=lambda x: x.created_at, reverse=True)
    approved = sorted(w_approved + n_approved + i_approved + p_approved, key=lambda x: x.created_at, reverse=True)
    rejected = sorted(w_rejected + n_rejected + i_rejected + p_rejected, key=lambda x: x.created_at, reverse=True)

    # Authority Enrichment
    for group in [pending, approved, rejected, timeline_pending, timeline_approved, timeline_rejected]:
        for item in group:
            item.has_authority = has_authority_over_proposal(request.user, item)

    logs_base = CaosEventLog.objects.all().order_by('-timestamp')[:50]
    logs_world = [l for l in logs_base if 'WORLD' in l.action.upper()]
    logs_narrative = [l for l in logs_base if 'NARRATIVE' in l.action.upper()]
    logs_image = [l for l in logs_base if 'IMAGE' in l.action.upper()]
    logs_other = [l for l in logs_base if l not in logs_world + logs_narrative + logs_image]

    grouped_inbox = group_items_by_author(pending)
    grouped_approved = group_items_by_author(approved)
    grouped_rejected = group_items_by_author(rejected)
    
    # Group Timeline proposals
    grouped_timeline_pending = group_items_by_author(timeline_pending)
    grouped_timeline_approved = group_items_by_author(timeline_approved)
    grouped_timeline_rejected = group_items_by_author(timeline_rejected)
    
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
        # Timeline data
        'timeline_pending': timeline_pending,
        'timeline_approved': timeline_approved,
        'timeline_rejected': timeline_rejected,
        'grouped_timeline_pending': grouped_timeline_pending,
        'grouped_timeline_approved': grouped_timeline_approved,
        'grouped_timeline_rejected': grouped_timeline_rejected,
        'timeline_pending_count': len(timeline_pending),
    }
    return render(request, 'dashboard.html', context)
