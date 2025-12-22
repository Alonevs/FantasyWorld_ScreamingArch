from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosEventLog, CaosVersionORM, CaosNarrativeVersionORM, CaosImageProposalORM
)
from itertools import chain
from operator import attrgetter

@login_required
def audit_log_view(request):
    """
    Detailed Audit Log with Filters.
    """
    logs = CaosEventLog.objects.all().order_by('-timestamp')
    users = User.objects.all().order_by('username')

    # FILTERS
    f_user = request.GET.get('user')
    f_type = request.GET.get('type') # Replaces f_action for high-level type filtering
    f_search = request.GET.get('q')
    
    if f_user:
        logs = logs.filter(user_id=f_user)
        
    if f_type:
        ft = f_type.upper()
        if ft == 'WORLD':
             logs = logs.filter(Q(action__icontains='WORLD') | Q(action__icontains='MUNDO'))
        elif ft == 'NARRATIVE':
             logs = logs.filter(Q(action__icontains='NARRATIVE') | Q(action__icontains='NARRATIVA'))
        elif ft == 'IMAGE':
             logs = logs.filter(Q(action__icontains='IMAGE') | Q(action__icontains='PHOTO') | Q(action__icontains='FOTO'))

    if f_search:
        logs = logs.filter(details__icontains=f_search)
        
    paginator = Paginator(logs, 50) # 50 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Enrichment: Infer Type from Action/ID
    for log in page_obj:
        act = log.action.upper()
        tid = str(log.target_id) if log.target_id else ""
        
        # Default
        log.inferred_icon = "📝"
        log.inferred_label = "Registro"
        
        # Heuristics
        if "WORLD" in act or "MUNDO" in act:
            log.inferred_icon = "🌍"
            log.inferred_label = "Mundo"
        elif "NARRATIVE" in act or "NARRATIVA" in act:
             log.inferred_icon = "📜"
             log.inferred_label = "Narrativa"
        elif "IMAGE" in act or "PHOTO" in act or "FOTO" in act:
             log.inferred_icon = "🖼️"
             log.inferred_label = "Imagen"
        # Fallbacks for generic actions based on ID ID
        elif tid.isdigit(): # Usually Image ID or Proposal ID
             log.inferred_icon = "🖼️" 
             log.inferred_label = "Imagen (Probable)"
        elif len(tid) == 10 and tid.isalnum(): # JID/NanoID format
             log.inferred_icon = "🌍"
             log.inferred_label = "Mundo"
        elif len(tid) > 10: # Narrative NID usually longer or UUID? Or generic
             log.inferred_icon = "📜"
             log.inferred_label = "Narrativa (Probable)"

    context = {
        'page_obj': page_obj,
        'users': users,
        'current_user': int(f_user) if f_user else None,
        'current_type': f_type,
        'search_query': f_search
    }
    return render(request, 'dashboard/audit_log.html', context)

@login_required
def version_history_view(request):
    """
    Unified Version History (Archived Items), Grouped by Entity.
    """
    # 1. Base QuerySets (Status = ARCHIVED or HISTORY)
    w_qs = CaosVersionORM.objects.filter(status__in=['ARCHIVED', 'HISTORY']).select_related('author', 'world')
    n_qs = CaosNarrativeVersionORM.objects.filter(status__in=['ARCHIVED', 'HISTORY']).select_related('author', 'narrative__world')
    
    users = User.objects.all().order_by('username')
    
    # 2. FILTERS
    f_user = request.GET.get('user')
    f_type = request.GET.get('type') # WORLD, NARRATIVE
    f_action = request.GET.get('action') # Ignored for now or mapped later
    
    if f_user:
        w_qs = w_qs.filter(author_id=f_user)
        n_qs = n_qs.filter(author_id=f_user)
        
    if f_type == 'WORLD':
        n_qs = n_qs.none()
    elif f_type == 'NARRATIVE':
        w_qs = w_qs.none()

    # 3. GROUPING LOGIC
    # structure: { 'unique_key': { 'entity_name': Str, 'type': Str, 'latest_date': Date, 'versions': [List] } }
    grouped_data = {}

    # Process Worlds
    for v in w_qs:
        key = f"WORLD_{v.world.id}"
        if key not in grouped_data:
            grouped_data[key] = {
                'id': v.world.id,
                'public_id': v.world.public_id, # For links
                'name': v.world.name,
                'type': 'WORLD',
                'type_label': '🌍 Mundo',
                'versions': [],
                'latest_date': v.created_at
            }
        
        # Enrich Version
        v.target_name = v.proposed_name
        v.action_type = v.cambios.get('action', 'UPDATE') if v.cambios else 'UPDATE'
        grouped_data[key]['versions'].append(v)
        # Update latest date for sorting
        if v.created_at > grouped_data[key]['latest_date']:
            grouped_data[key]['latest_date'] = v.created_at

    # Process Narratives
    for v in n_qs:
        key = f"NARRATIVE_{v.narrative.nid}"
        if key not in grouped_data:
            grouped_data[key] = {
                'id': v.narrative.nid,
                'public_id': v.narrative.public_id if hasattr(v.narrative, 'public_id') else v.narrative.nid,
                'name': v.narrative.titulo,
                'type': 'NARRATIVE',
                'type_label': '📖 Narrativa',
                'versions': [],
                'latest_date': v.created_at
            }
        
        # Enrich Version
        v.target_name = v.proposed_title
        v.action_type = v.action if hasattr(v, 'action') else 'UPDATE'
        grouped_data[key]['versions'].append(v)
        if v.created_at > grouped_data[key]['latest_date']:
            grouped_data[key]['latest_date'] = v.created_at

    # 4. CONVERT TO LIST & SORT GROUPS
    # Sort groups by their most recent version date (Newest first)
    history_groups = list(grouped_data.values())
    history_groups.sort(key=lambda x: x['latest_date'], reverse=True)

    # 5. SORT VERSIONS INSIDE GROUPS (Newest first)
    for group in history_groups:
        group['versions'].sort(key=lambda x: x.created_at, reverse=True)

    # 6. PAGINATION
    paginator = Paginator(history_groups, 10) # 10 Groups per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'users': users,
        'current_user': int(f_user) if f_user else None,
        'current_type': f_type,
        'current_action': f_action,
    }
    return render(request, 'dashboard/history.html', context)

@login_required
def version_history_cleanup_view(request):
    """
    Maintenance tool: Keep only the 5 most recent archived versions for each entity.
    """
    from django.contrib import messages
    from .utils import log_event
    
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Acceso denegado.")
        return redirect('version_history')

    if request.method != 'POST':
        return redirect('version_history')

    deleted_count = 0
    
    # 1. Cleanup Worlds
    world_ids = CaosVersionORM.objects.filter(status__in=['ARCHIVED', 'HISTORY']).values_list('world_id', flat=True).distinct()
    for w_id in world_ids:
        # Get all archived versions for this world, ordered by newest first
        v_ids = list(CaosVersionORM.objects.filter(world_id=w_id, status__in=['ARCHIVED', 'HISTORY'])
                     .order_by('-created_at')
                     .values_list('id', flat=True))
        
        # If more than 5, delete the rest
        if len(v_ids) > 5:
            to_delete = v_ids[5:]
            count, _ = CaosVersionORM.objects.filter(id__in=to_delete).delete()
            deleted_count += count

    # 2. Cleanup Narratives
    narrative_ids = CaosNarrativeVersionORM.objects.filter(status__in=['ARCHIVED', 'HISTORY']).values_list('narrative_id', flat=True).distinct()
    for n_id in narrative_ids:
        v_ids = list(CaosNarrativeVersionORM.objects.filter(narrative_id=n_id, status__in=['ARCHIVED', 'HISTORY'])
                     .order_by('-created_at')
                     .values_list('id', flat=True))
        
        if len(v_ids) > 5:
            to_delete = v_ids[5:]
            count, _ = CaosNarrativeVersionORM.objects.filter(id__in=to_delete).delete()
            deleted_count += count

    messages.success(request, f"🚀 Mantenimiento completado. Se han liberado {deleted_count} registros antiguos.")
    log_event(request.user, "HISTORY_CLEANUP", f"Mantenimiento de historial: {deleted_count} versiones borradas.")
    
    return redirect('version_history')
