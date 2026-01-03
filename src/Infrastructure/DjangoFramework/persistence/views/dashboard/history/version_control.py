from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib import messages
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosVersionORM, CaosNarrativeVersionORM, CaosImageProposalORM,
    TimelinePeriodVersion
)
from ..utils import get_visible_user_ids, log_event

@login_required
def version_history_view(request):
    """
    Historial Unificado de Versiones y Propuestas Archivadas.
    Agrupa los cambios por Entidad (Mundo/Narrativa) y previene la visualización
    de versiones que aún están activas (LIVE) para evitar redundancia.
    """
    # Requisito del usuario: Ocultar las versiones LIVE del historial para evitar redundancia.
    # Mostramos 'HISTORY' (versiones anteriores al Live) y 'ARCHIVED' (propuestas ejecutadas/archivadas).
    target_statuses = ['HISTORY', 'ARCHIVED']
    
    w_qs = CaosVersionORM.objects.filter(status__in=target_statuses).select_related('author', 'world')
    n_qs = CaosNarrativeVersionORM.objects.filter(status__in=target_statuses).select_related('author', 'narrative__world')
    i_qs = CaosImageProposalORM.objects.filter(status__in=target_statuses).select_related('author', 'world')
    p_qs = TimelinePeriodVersion.objects.filter(status__in=target_statuses).select_related('author', 'period__world')
    
    is_global, visible_ids = get_visible_user_ids(request.user)
    
    if not is_global:
        w_qs = w_qs.filter(author_id__in=visible_ids)
        n_qs = n_qs.filter(author_id__in=visible_ids)
        i_qs = i_qs.filter(author_id__in=visible_ids)
        p_qs = p_qs.filter(author_id__in=visible_ids)
        users = User.objects.filter(id__in=visible_ids).order_by('username')
    else:
        users = User.objects.all().order_by('username')
    
    # 2. FILTERS
    f_user = request.GET.get('user')
    f_type = request.GET.get('type') # WORLD, NARRATIVE
    f_action = request.GET.get('action') # CREATE, UPDATE, DELETE, RESTORE, UPDATE_NOOS, etc.
    
    if f_user:
        w_qs = w_qs.filter(author_id=f_user)
        n_qs = n_qs.filter(author_id=f_user)
        i_qs = i_qs.filter(author_id=f_user)
        p_qs = p_qs.filter(author_id=f_user)
        
    if f_type == 'WORLD':
        n_qs = n_qs.none(); i_qs = i_qs.none(); p_qs = p_qs.none()
    elif f_type == 'METADATA':
        n_qs = n_qs.none(); i_qs = i_qs.none(); p_qs = p_qs.none()
    elif f_type == 'NARRATIVE':
        w_qs = w_qs.none(); i_qs = i_qs.none(); p_qs = p_qs.none()
    elif f_type == 'IMAGE':
        w_qs = w_qs.none(); n_qs = n_qs.none(); p_qs = p_qs.none()
    elif f_type == 'PERIOD':
        w_qs = w_qs.none(); n_qs = n_qs.none(); i_qs = i_qs.none()

    # Apply Action Filter (Pre-filtering)
    
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

    # 4. INITIALIZE EMPTY GROUPS (Ensures they appear even if empty)
    grouped_data = {}
    
    # Priority Map & Placeholders
    type_priority = {
        'WORLD': 0,
        'NARRATIVE': 1,
        'IMAGE': 2,
        'METADATA': 3,
        'PERIOD': 4
    }
    
    required_types = ['WORLD', 'NARRATIVE', 'METADATA', 'IMAGE', 'PERIOD']
    if f_type:
        required_types = [f_type]

    # Process Worlds
    for v in w_qs:
        # Determine if this is primarily a metadata update
        raw_action = v.cambios.get('action', 'UPDATE') if v.cambios else 'UPDATE'
        keys = v.cambios.keys() if v.cambios else []
        is_metadata = ('metadata' in keys or raw_action == 'METADATA_UPDATE') and raw_action != 'DELETE'
        
        actual_type = 'METADATA' if is_metadata else 'WORLD'
        
        # Check if it matches selected filter
        if f_type and f_type in ['WORLD', 'METADATA'] and actual_type != f_type:
            continue

        key = f"{actual_type}_{v.world.id}"
        
        if key not in grouped_data:
            grouped_data[key] = {
                'id': v.world.id,
                'public_id': v.world.public_id, # For links
                'name': v.world.name,
                'type': actual_type,
                'type_label': '🌍 Mundo' if actual_type == 'WORLD' else '🧬 Metadatos',
                'versions': [],
                'latest_date': v.created_at
            }
        
        # Enrich Version
        v.target_name = v.proposed_name
        
        # Refine Action label if it's an UPDATE
        if raw_action == 'UPDATE':
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
        
        # Override action label based on status for better context
        if v.status == 'ARCHIVED':
             v.action_label = f"📂 Archivada: {v.action_label}"
        elif v.status == 'REJECTED':
             v.action_label = f"❌ Rechazada: {v.action_label}"
        elif v.status == 'APPROVED':
             v.action_label = f"☑️ Aprobada: {v.action_label}"
        elif v.status == 'HISTORY':
             v.action_label = f"📜 Histórica: {v.action_label}"

        v.action_type = v.refined_action # standardized for loop
        grouped_data[key]['versions'].append(v)
        # Update latest date for sorting and capture latest action
        if v.created_at > grouped_data[key]['latest_date']:
            grouped_data[key]['latest_date'] = v.created_at
            grouped_data[key]['latest_action_label'] = v.action_label

    # Process Narrativas
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
        
        n_label_map = {
            'ADD': '✨ Creación',
            'EDIT': '✏️ Edición',
            'DELETE': '🗑️ Borrado',
            'RESTORE': '♻️ Restauración'
        }
        v.action_label = n_label_map.get(v.action_type, '✏️ Edición')
        
        if v.status == 'ARCHIVED':
            v.action_label = f"📂 Archivada: {v.action_label}"
        elif v.status == 'REJECTED':
             v.action_label = f"❌ Rechazada: {v.action_label}"
        elif v.status == 'APPROVED':
             v.action_label = f"☑️ Aprobada: {v.action_label}"
        elif v.status == 'HISTORY':
             v.action_label = f"📜 Histórica: {v.action_label}"
        grouped_data[key]['versions'].append(v)
        if v.created_at > grouped_data[key]['latest_date']:
            grouped_data[key]['latest_date'] = v.created_at
            grouped_data[key]['latest_action_label'] = v.action_label

    # Process Images
    for v in i_qs:
        key = f"IMAGE_{v.id}"
        if key not in grouped_data:
             grouped_data[key] = {
                'id': v.id,
                'public_id': v.world.public_id if v.world else '???',
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
        v.version_number = 1
        
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

    # Process Periods
    for v in p_qs:
        key = f"PERIOD_{v.period.id}"
        if key not in grouped_data:
            grouped_data[key] = {
                'id': v.period.id,
                'public_id': v.period.world.public_id if v.period.world else '???',
                'name': f"📅 {v.period.title}",
                'type': 'PERIOD',
                'type_label': '📅 Periodo',
                'versions': [],
                'latest_date': v.created_at
            }
        
        # Enrich Version
        v.target_name = v.proposed_title
        v.action_type = v.action if hasattr(v, 'action') else 'EDIT'
        
        p_label_map = {
            'ADD': '✨ Creación',
            'EDIT': '✏️ Edición',
            'DELETE': '🗑️ Borrado'
        }
        v.action_label = p_label_map.get(v.action_type, '✏️ Edición')
        
        if v.status == 'ARCHIVED':
            v.action_label = f"📂 Archivada: {v.action_label}"
        elif v.status == 'REJECTED':
             v.action_label = f"❌ Rechazada: {v.action_label}"
        elif v.status == 'APPROVED':
             v.action_label = f"☑️ Aprobada: {v.action_label}"
        elif v.status == 'HISTORY':
             v.action_label = f"📜 Histórica: {v.action_label}"
        
        grouped_data[key]['versions'].append(v)
        if v.created_at > grouped_data[key]['latest_date']:
            grouped_data[key]['latest_date'] = v.created_at
            grouped_data[key]['latest_action_label'] = v.action_label

    # 4.1 ADD EMPTY MARKERS FOR MISSING TYPES
    # This ensures regroup in template works even for empty categories
    found_types = set(g['type'] for g in grouped_data.values())
    for rt in required_types:
        if rt not in found_types:
            grouped_data[f"EMPTY_{rt}"] = {
                'id': 0, 'public_id': '', 'name': '',
                'type': rt, 'type_label': '',
                'versions': [], 'latest_date': None,
                'latest_author_name': 'Sistema',
                'is_empty_marker': True
            }

    # 5. CONVERT TO LIST & SORT GROUPS
    formatted_groups = list(grouped_data.values())
    
    for g in formatted_groups:
        g['sort_type_idx'] = type_priority.get(g['type'], 99)
        if g.get('is_empty_marker'):
            continue
            
        # Ensure versions are sorted
        g['versions'].sort(key=lambda x: x.created_at, reverse=True)
        if g['versions']:
            latest = g['versions'][0]
            if latest.author:
                g['latest_author_name'] = latest.author.username
            else:
                g['latest_author_name'] = 'Sistema'
        else:
            g['latest_author_name'] = 'Sistema'

    # Sort groups: Type -> Empty Marker Status (Data first) -> Author -> Date
    formatted_groups.sort(key=lambda x: (
        x['sort_type_idx'], 
        1 if x.get('is_empty_marker') else 0, # Content groups first, then markers if any
        x.get('latest_author_name', 'Z').lower(), 
        x['latest_date'].timestamp() * -1 if x['latest_date'] else 0
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
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Acceso denegado.")
        return redirect('version_history')

    if request.method != 'POST':
        return redirect('version_history')

    deleted_count = 0
    
    # 1. Cleanup World Versions (ARCHIVED ONLY)
    world_ids = CaosVersionORM.objects.filter(status='ARCHIVED').values_list('world_id', flat=True).distinct()
    for w_id in world_ids:
        # Get all ARCHIVED versions for this world
        v_ids = list(CaosVersionORM.objects.filter(world_id=w_id, status='ARCHIVED')
                     .order_by('-created_at')
                     .values_list('id', flat=True))
        
        # If more than 5, delete the rest
        if len(v_ids) > 5:
            to_delete = v_ids[5:]
            count, _ = CaosVersionORM.objects.filter(id__in=to_delete).delete()
            deleted_count += count

    # 2. Cleanup Narratives (ARCHIVED ONLY)
    narrative_ids = CaosNarrativeVersionORM.objects.filter(status='ARCHIVED').values_list('narrative_id', flat=True).distinct()
    for n_id in narrative_ids:
        v_ids = list(CaosNarrativeVersionORM.objects.filter(narrative_id=n_id, status='ARCHIVED')
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
    Acción de Borrado Masivo Manual para el Historial.
    Exclusivo para Superusuarios (Admin Supremo).
    Permite purgar registros históricos o propuestas archivadas seleccionando IDs específicos.
    """
    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado. Solo Admin Supremo.")
        return redirect('version_history')
        
    if request.method == 'POST':
        selection = request.POST.getlist('selected_versions[]')
        
        w_ids = []
        n_ids = []
        
        for item in selection:
            if item.startswith('WORLD_'):
                try: w_ids.append(int(item.replace('WORLD_', '')))
                except: pass
            elif item.startswith('METADATA_'):
                try: w_ids.append(int(item.replace('METADATA_', '')))
                except: pass
            elif item.startswith('NARRATIVE_'):
                try: n_ids.append(int(item.replace('NARRATIVE_', '')))
                except: pass
                
        deleted_count = 0
        
        if w_ids:
            # Blindaje: Only allow deleting ARCHIVED (rejected/deleted proposals)
            count, _ = CaosVersionORM.objects.filter(id__in=w_ids, status='ARCHIVED').delete()
            deleted_count += count
            
        if n_ids:
             count, _ = CaosNarrativeVersionORM.objects.filter(id__in=n_ids, status='ARCHIVED').delete()
             deleted_count += count
             
        if deleted_count > 0:
            messages.success(request, f"🗑️ Se han eliminado {deleted_count} registros históricos seleccionados.")
            log_event(request.user, "HISTORY_BULK_DELETE", f"Eliminación manual: {deleted_count} items.")
        else:
            messages.warning(request, "No se seleccionó nada o los items no eran válidos.")
            
    return redirect('version_history')
