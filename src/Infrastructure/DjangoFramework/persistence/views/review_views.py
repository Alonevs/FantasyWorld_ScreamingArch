from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.html import escape
import difflib

from ..models import (
    CaosVersionORM, CaosNarrativeVersionORM, CaosImageProposalORM,
    CaosWorldORM, CaosNarrativeORM, CaosEventLog, TimelinePeriodVersion
)
from .view_utils import get_metadata_diff


from django.http import Http404

def get_diff_html(a, b):
    """
    Generates a simple HTML diff of two strings.
    """
    a = a or ""
    b = b or ""
    
    seqm = difflib.SequenceMatcher(None, a, b)
    output = []
    
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(escape(a[a0:a1]))
        elif opcode == 'insert':
            output.append(f'<span class="bg-green-900/50 text-green-200">{escape(b[b0:b1])}</span>')
        elif opcode == 'delete':
            output.append(f'<span class="bg-red-900/50 text-red-200 line-through opacity-70">{escape(a[a0:a1])}</span>')
        elif opcode == 'replace':
            output.append(f'<span class="bg-red-900/50 text-red-200 line-through opacity-70">{escape(a[a0:a1])}</span>')
            output.append(f'<span class="bg-green-900/50 text-green-200">{escape(b[b0:b1])}</span>')
            
    # BUG FIX v0: If 'a' was empty but 'b' has content, and no diff spans were added, 
    # Ensure we show 'b' as new. difflib usually handles this with 'insert', 
    # but for empty 'a', it sometimes produces just 'insert'.
    if not a and b and not output:
        return f'<span class="bg-green-900/50 text-green-200">{escape(b)}</span>'
        
    return "".join(output)

    return "".join(output)

from .dashboard.workflow import (
    rechazar_propuesta, rechazar_narrativa, rechazar_periodo
)

from .dashboard.assets import rechazar_imagen

@login_required
def review_proposal(request, type, id):
    """
    Unified view to review and approve/reject proposals.
    type: 'WORLD', 'NARRATIVE', 'IMAGE'
    id: Proposal ID (CaosVersionORM.id, etc)
    """
    
    proposal = None
    live_obj = None
    
    # Context Data
    ctx = {
        'proposal_type': type,
        'diff_title': "",
        'diff_content': "",
        'live_title': "",
        'live_content': "",
        'proposed_title': "",
        'proposed_content': "",
        'change_log': "",
        'image_url': None,
        'live_image_url': None,
    }

    try:
        # 1. FETCH PROPOSAL & LIVE DATA
        # 1. FETCH PROPOSAL & LIVE DATA
        if type in ['WORLD', 'METADATA']:
            # TRY CaosVersionORM first
            try:
                proposal = CaosVersionORM.objects.get(id=id)
            except CaosVersionORM.DoesNotExist:
                # If not found, try TimelinePeriodVersion (for PERIOD metadata updates)
                if TimelinePeriodVersion.objects.filter(id=id).exists():
                    return redirect('revisar_propuesta', type='PERIOD', id=id)
                raise Http404("Propuesta no encontrada")

            live_obj = proposal.world if proposal.world else None
            if live_obj:
                ctx['live_title'] = live_obj.name
                ctx['live_content'] = live_obj.description
                ctx['live_version_number'] = live_obj.current_version_number
            ctx['change_log'] = proposal.change_log
            if live_obj:
                ctx['live_version_number'] = live_obj.current_version_number
            
            # Calculate Diffs
            ctx['diff_title'] = get_diff_html(ctx['live_title'], ctx['proposed_title'])
            ctx['diff_content'] = get_diff_html(ctx['live_content'], ctx['proposed_content'])
            
            # Metadata Diff & Listing
            from .view_utils import get_metadata_properties_dict
            live_meta = live_obj.metadata if live_obj else {}
            proposed_meta = proposal.cambios.get('metadata', {}) if proposal.cambios else {}
            
            live_props = get_metadata_properties_dict(live_meta)
            prop_props = get_metadata_properties_dict(proposed_meta)
            
            ctx['live_metadata_list'] = [{'key': k, 'value': v} for k, v in live_props.items()]
            
            # Prepare Decorated List for Right Side
            diff_results = get_metadata_diff(live_meta, proposed_meta)
            diff_map = {d['key']: d for d in diff_results}
            ctx['metadata_diff'] = diff_results # Keep for compatibility if needed
            
            all_keys = sorted(set(live_props.keys()) | set(prop_props.keys()))
            decorated_list = []
            for k in all_keys:
                diff = diff_map.get(k, {})
                action = diff.get('action', 'NORMAL')
                val = prop_props.get(k, live_props.get(k))
                if action == 'DELETE': val = live_props.get(k)
                
                item = {
                    'key': k,
                    'value': val,
                    'action': action,
                    'old': diff.get('old'),
                    'new': diff.get('new')
                }
                decorated_list.append(item)
            
            ctx['proposed_metadata_list_decorated'] = decorated_list
            
            # If only metadata changed, label it correctly
            if not ctx['diff_title'] and not ctx['diff_content'] and ctx['metadata_diff']:
                ctx['proposal_type'] = 'METADATA'
            
            # 🖼️ IF SET_COVER: Force image preview mode even if technical type is WORLD
            if proposal.cambios and proposal.cambios.get('action') == 'SET_COVER':
                filename = proposal.cambios.get('cover_image')
                ctx['image_url'] = f"/static/persistence/img/{proposal.world.id}/{filename}"
                
                # Live image (Original cover)
                live_filename = live_obj.metadata.get('cover_image') if live_obj and live_obj.metadata else None
                if live_filename:
                    ctx['live_image_url'] = f"/static/persistence/img/{proposal.world.id}/{live_filename}"
                
                ctx['diff_content'] = f"📸 Propuesta de Cambio de Portada: {filename}"
                ctx['is_image'] = True
            
        elif type == 'NARRATIVE':
            proposal = get_object_or_404(CaosNarrativeVersionORM, id=id)
            if proposal.narrative:
                live_obj = proposal.narrative
                ctx['live_title'] = live_obj.titulo
                ctx['live_content'] = live_obj.contenido
                
            # context label
            ctx['context_label'] = f"NARRATIVA ({proposal.narrative.timeline_period.title})" if proposal.narrative.timeline_period else "NARRATIVA (Actual)"
            
            # Calculate Diffs
            ctx['diff_title'] = get_diff_html(ctx['live_title'], ctx['proposed_title'])
            ctx['diff_content'] = get_diff_html(ctx['live_content'], ctx['proposed_content'])

        elif type == 'IMAGE':
            proposal = get_object_or_404(CaosImageProposalORM, id=id)
            # Handle Preview for DELETE actions (show target image)
            if proposal.action == 'DELETE':
                # Assuming standard path structure
                ctx['image_url'] = f"/static/persistence/img/{proposal.world.id}/{proposal.target_filename}"
                ctx['diff_content'] = f"Propuesta para ELIMINAR imagen: {proposal.target_filename}"
            else: # Implies ADD
                ctx['image_url'] = proposal.image.url if proposal.image else None
                ctx['diff_content'] = f"Propuesta de Nueva Imagen: {proposal.title}" if proposal.title else "Propuesta de Nueva Imagen"
                
            ctx['change_log'] = proposal.change_log if getattr(proposal, 'change_log', None) else f"Acción: {proposal.get_action_display()}"
            ctx['is_image'] = True
            ctx['context_label'] = f"IMAGEN ({proposal.timeline_period.title})" if proposal.timeline_period else "IMAGEN (Actual)"

        elif type == 'PERIOD':
            proposal = get_object_or_404(TimelinePeriodVersion, id=id)
            period = proposal.period
            
            if proposal.action != 'ADD':
                live_obj = period
                ctx['live_title'] = live_obj.title
                ctx['live_content'] = live_obj.description
            
            ctx['proposed_title'] = proposal.proposed_title
            ctx['proposed_content'] = proposal.proposed_description
            ctx['change_log'] = proposal.change_log
            
            # Metadata Table Support for Periods
            from .view_utils import get_metadata_properties_dict
            live_meta = period.metadata if period else {}
            proposed_meta = proposal.proposed_metadata or {}
            
            live_props = get_metadata_properties_dict(live_meta)
            prop_props = get_metadata_properties_dict(proposed_meta)
            
            ctx['live_metadata_list'] = [{'key': k, 'value': v} for k, v in live_props.items()]
            diff_results = get_metadata_diff(live_meta, proposed_meta)
            diff_map = {d['key']: d for d in diff_results}
            
            all_keys = sorted(set(live_props.keys()) | set(prop_props.keys()))
            decorated_list = []
            for k in all_keys:
                diff = diff_map.get(k, {})
                action = diff.get('action', 'NORMAL')
                val = prop_props.get(k, live_props.get(k))
                item = {'key': k, 'value': val, 'action': action, 'old': diff.get('old'), 'new': diff.get('new')}
                decorated_list.append(item)
            
            ctx['proposed_metadata_list_decorated'] = decorated_list
            ctx['metadata_diff'] = diff_results
            
            # Calculate Diffs
            ctx['diff_title'] = get_diff_html(ctx['live_title'], ctx['proposed_title'])
            ctx['diff_content'] = get_diff_html(ctx['live_content'], ctx['proposed_content'])
            
            # Extra context
            ctx['parent_name'] = period.world.name
            ctx['context_label'] = f"PERIODO ({period.title})"

    except Http404:
        messages.warning(request, "La propuesta solicitada no existe o ya ha sido procesada.")
        return redirect('dashboard')


    # 2. DETECT DELETE INTENT
    change_log_str = str(ctx.get('change_log', '') or "")
    action_str = str(getattr(proposal, 'action', '') or "")
    ctx['is_delete'] = ('DELETE' in action_str) or ('Eliminación' in change_log_str) or ('Borrar' in change_log_str)
    
    # 3. DETECT PENDING STATUS
    ctx['is_pending'] = (getattr(proposal, 'status', 'PENDING') == 'PENDING')

    # 4. HANDLE POST (APPROVE/REJECT)
    # Import logic views directly to preserve 'reason' in POST request
    if request.method == 'POST':
        action = request.POST.get('action') # 'approve' or 'reject'
        
        if action == 'approve':
            # Redirect is fine for approve (no extra data)
            if type in ['WORLD', 'METADATA']: return redirect('aprobar_version', id=id)
            elif type == 'NARRATIVE': return redirect('aprobar_narrativa', id=id)
            elif type == 'IMAGE': return redirect('aprobar_imagen', id=id)
            elif type == 'PERIOD': return redirect('aprobar_periodo', id=id)
            
        elif action == 'reject':
            # DIRECT CALL to pass POST data (reason)
            ctx['context_label'] = ctx.get('context_label', 'Actual')
            if type in ['WORLD', 'METADATA']: return rechazar_propuesta(request, id=id)
            elif type == 'NARRATIVE': return rechazar_narrativa(request, id=id)
            elif type == 'IMAGE': return rechazar_imagen(request, id=id)
            elif type == 'PERIOD': return rechazar_periodo(request, id=id)

        elif action == 'archive':
            # REDIRECT to the archive workflow
            if type in ['WORLD', 'METADATA']: return redirect('archivar_propuesta', id=id)
            elif type == 'NARRATIVE': return redirect('archivar_narrativa', id=id)
            elif type == 'IMAGE': return redirect('archivar_imagen', id=id)
            elif type == 'PERIOD': return redirect('archivar_periodo', id=id)

    ctx['proposal'] = proposal
    return render(request, 'staff/review_proposal.html', ctx)
