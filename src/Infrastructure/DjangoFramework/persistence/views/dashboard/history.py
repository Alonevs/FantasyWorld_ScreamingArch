from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Max
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
    # 1. Base QuerySets (Status = ARCHIVED or HISTORY or REJECTED for complete history)
    # Note: 'REJECTED' might be considered history too depending on requirements. 
    # Sticking to ['ARCHIVED', 'HISTORY'] for now as per previous pattern, but ensuring we capture what's needed.
    # Actually, for images, 'ARCHIVED' usually means old versions or deleted ones.
    
    target_statuses = ['ARCHIVED', 'HISTORY']
    
    w_qs = CaosVersionORM.objects.filter(status__in=target_statuses).select_related('author', 'world')
    n_qs = CaosNarrativeVersionORM.objects.filter(status__in=target_statuses).select_related('author', 'narrative__world')
    i_qs = CaosImageProposalORM.objects.filter(status__in=target_statuses).select_related('author', 'world')
    
    users = User.objects.all().order_by('username')
    
    # 2. FILTERS
    f_user = request.GET.get('user')
    f_type = request.GET.get('type') # WORLD, NARRATIVE
    f_action = request.GET.get('action') # CREATE, UPDATE, DELETE, RESTORE, UPDATE_NOOS, etc.
    
    if f_user:
        w_qs = w_qs.filter(author_id=f_user)
        n_qs = n_qs.filter(author_id=f_user)
        i_qs = i_qs.filter(author_id=f_user)
        
    if f_type == 'WORLD':
        n_qs = n_qs.none(); i_qs = i_qs.none()
    elif f_type == 'NARRATIVE':
        w_qs = w_qs.none(); i_qs = i_qs.none()
    elif f_type == 'IMAGE':
        w_qs = w_qs.none(); n_qs = n_qs.none()

    # Apply Action Filter (Pre-filtering)
    # Note: Actions are stored diffently.
    # World: v.cambios.get('action') or v.change_log
    # Narrative: v.action
    
    if f_action:
        # Filter Worlds
        # Django JSONField filtering: cambios__action=f_action
        if f_action in ['CREATE', 'DELETE', 'RESTORE']:
             w_qs = w_qs.filter(cambios__action=f_action)
        elif f_action == 'UPDATE':
             # General updates (now includes description updates)
             w_qs = w_qs.filter(Q(cambios__action='UPDATE') | Q(cambios__action__isnull=True))
        elif f_action == 'UPDATE_NOOS':
             # Specific logic: Action is 'UPDATE' AND 'noos' is in keys
             w_qs = w_qs.filter(cambios__has_key='noos')


        # Filter Narratives
        # Narrative actions are simpler: ADD, EDIT, DELETE, RESTORE
        narrative_map = {
            'CREATE': 'ADD',
            'UPDATE': 'EDIT',
            'DELETE': 'DELETE',
            'RESTORE': 'RESTORE' # Standardize if exists, else match string
        }
        
        target_narrative_action = narrative_map.get(f_action, f_action)
        n_qs = n_qs.filter(action=target_narrative_action)

        # Filter Images
        # Action choices: ADD, DELETE
        # Map: CREATE -> ADD, DELETE -> DELETE, RESTORE -> ??
        img_map = {
            'CREATE': 'ADD',
            'DELETE': 'DELETE'
        }
        target_img_action = img_map.get(f_action)
        if target_img_action:
            i_qs = i_qs.filter(action=target_img_action)
        else:
            # If action is UPDATE or something images don't have, hide images
            i_qs = i_qs.none()

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
        v.target_name = v.proposed_name
        
        # Determine Action Type for UI
        raw_action = v.cambios.get('action', 'UPDATE') if v.cambios else 'UPDATE'
        
        # Refine Action label if it's an UPDATE
        if raw_action == 'UPDATE':
            # Check what changed
            keys = v.cambios.keys() if v.cambios else []
            if 'noos' in keys:
                 v.refined_action = 'UPDATE_NOOS'
                 v.action_label = '🧠 Ajuste Noos'
            elif 'metadata' in keys:
                 v.refined_action = 'UPDATE_META'
                 v.action_label = '🧬 Metadatos'
            else:
                 v.refined_action = 'UPDATE'
                 v.action_label = '✏️ Edición'
        else:
            v.refined_action = raw_action
            label_map = {
                'CREATE': '✨ Creación',
                'DELETE': '🗑️ Borrado',
                'RESTORE': '♻️ Restauración'
            }
            v.action_label = label_map.get(raw_action, raw_action)

        v.action_type = v.refined_action # standardized for loop
        grouped_data[key]['versions'].append(v)
        # Update latest date for sorting and capture latest action
        if v.created_at > grouped_data[key]['latest_date']:
            grouped_data[key]['latest_date'] = v.created_at
            grouped_data[key]['latest_action_label'] = v.action_label

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
        
        # Narrative mappings
        n_label_map = {
            'ADD': '✨ Creación',
            'EDIT': '✏️ Edición',
            'DELETE': '🗑️ Borrado',
            'RESTORE': '♻️ Restauración'
        }
        v.action_label = n_label_map.get(v.action_type, '✏️ Edición')
        grouped_data[key]['versions'].append(v)
        if v.created_at > grouped_data[key]['latest_date']:
            grouped_data[key]['latest_date'] = v.created_at
            grouped_data[key]['latest_action_label'] = v.action_label

    # Process Images
    for v in i_qs:
        key = f"IMAGE_{v.id}" # Images are usually single events, but if we group by World or Image ID...
        # Image proposals don't have a "Version" chain like objects. Each proposal IS the record.
        # But to fit the UI, we treat it as a group of 1 version (or try to group by World?)
        # User wants "Fotos" similar to others. Grouping by World for images might be confusing if distinct images.
        # Let's group by the Image Proposal ID itself (single item group)
        
        # Enriched ID logic for unique key if needed
        
        if key not in grouped_data:
             grouped_data[key] = {
                'id': v.id,
                'public_id': v.world.public_id if v.world else '???', # Link to world
                'name': f"Foto: {v.title or v.target_filename or 'Sin Título'}",
                'type': 'IMAGE',
                'type_label': '🖼️ Imagen',
                'versions': [],
                'latest_date': v.created_at,
                'latest_action_label': '📸 Imagen',
                'latest_author_name': v.author.username if v.author else 'Sistema',
                'image_url': v.image.url if v.image else None,
            }
            
        v.target_name = v.title or v.target_filename
        v.version_number = 1 # Dummy
        
        act = v.action
        if act == 'ADD':
            v.action_label = '📸 Nueva Foto'
            v.action_type = 'CREATE'
        elif act == 'DELETE':
            v.action_label = '🗑️ Borrado Foto'
            v.action_type = 'DELETE'
        else:
            v.action_label = act
            v.action_type = act
            
        grouped_data[key]['versions'].append(v)

    # 4. CONVERT TO LIST & SORT GROUPS
    # Sorting Requirement: 
    # 1. Type Priority (World > Narrative > Image)
    # 2. Author Name
    # 3. Date (Newest first)
    
    # Priority Map
    type_priority = {
        'WORLD': 0,
        'NARRATIVE': 1,
        'IMAGE': 2
    }
    
    formatted_groups = list(grouped_data.values())
    
    # Enrichment for sorting (ensure author name exists on group level)
    for g in formatted_groups:
        g['sort_type_idx'] = type_priority.get(g['type'], 99)
        # Author: Use the author of the latest version if not present
        if 'latest_author_name' not in g:
             # Find latest version
             if g['versions']:
                 # Versions are not sorted yet in this loop, but we track latest_date. 
                 # Let's find the version matching latest_date or just take the first one after sorting.
                 pass
             g['latest_author_name'] = 'Unknown'

    # 5. SORT VERSIONS INSIDE GROUPS (Newest first)
    for group in formatted_groups:
        group['versions'].sort(key=lambda x: x.created_at, reverse=True)
        # Capture author from latest version for group sorting
        if group['versions']:
            latest = group['versions'][0]
            if latest.author:
                group['latest_author_name'] = latest.author.username
            else:
                group['latest_author_name'] = 'Sistema'

    # 6. SORT GROUPS
    # Sort key: (Type Index ASC, Author Name ASC, Date DESC)
    # Note: Python sorts are stable. We can chain sorts or use a tuple key.
    # Tuple: (sort_typ_idx, latest_author_name, -timestamp)
    # Since specific requirement: "agrupen primero por si es mundo o narrativa y luego ya por usuario"
    # It implies: Type -> User. What about Date? Usually date is important.
    # If Type -> User, then all user's worlds are together?
    # Let's try: Type ASC, User ASC, Date DESC
    
    formatted_groups.sort(key=lambda x: (
        x['sort_type_idx'], 
        x['latest_author_name'].lower(), 
        x['latest_date'].timestamp() * -1 # Negative for reverse sort on date
    ))
    
    history_groups = formatted_groups

    # 6. PAGINATION
    paginator = Paginator(history_groups, 100) # 100 Groups per page
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

@login_required
def delete_history_bulk_view(request):
    """
    Manual Bulk Deletion of History Items (Superuser Only).
    """
    from django.contrib import messages
    from .utils import log_event
    
    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado. Solo Admin Supremo.")
        return redirect('version_history')
        
    if request.method == 'POST':
        # Get selected IDs from form
        # Form inputs: selected_versions[] (value="WORLD_123" or "NARRATIVE_456" ?? No, IDs are unique per table)
        # We need to distinct between WorldVersion and NarrativeVersion IDs
        # Strategy: The checkbox value should carry the type: value="WORLD_10" or "NARRATIVE_55"
        
        selection = request.POST.getlist('selected_versions[]')
        
        w_ids = []
        n_ids = []
        
        for item in selection:
            if item.startswith('WORLD_'):
                try: w_ids.append(int(item.replace('WORLD_', '')))
                except: pass
            elif item.startswith('NARRATIVE_'):
                try: n_ids.append(int(item.replace('NARRATIVE_', '')))
                except: pass
                
        deleted_count = 0
        
        if w_ids:
            count, _ = CaosVersionORM.objects.filter(id__in=w_ids, status__in=['ARCHIVED', 'HISTORY']).delete()
            deleted_count += count
            
        if n_ids:
             count, _ = CaosNarrativeVersionORM.objects.filter(id__in=n_ids, status__in=['ARCHIVED', 'HISTORY']).delete()
             deleted_count += count
             
        if deleted_count > 0:
            messages.success(request, f"🗑️ Se han eliminado {deleted_count} registros históricos seleccionados.")
            log_event(request.user, "HISTORY_BULK_DELETE", f"Eliminación manual: {deleted_count} items.")
        else:
            messages.warning(request, "No se seleccionó nada o los items no eran válidos.")
            
    return redirect('version_history')
