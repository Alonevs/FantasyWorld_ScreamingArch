from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.html import escape
import difflib

from ..models import (
    CaosVersionORM, CaosNarrativeVersionORM, CaosImageProposalORM,
    CaosWorldORM, CaosNarrativeORM, CaosEventLog
)

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
            
    return "".join(output)

from .dashboard.workflow import rechazar_propuesta, rechazar_narrativa
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
        if type == 'WORLD':
            proposal = get_object_or_404(CaosVersionORM, id=id)
            if proposal.world:
                live_obj = proposal.world
                ctx['live_title'] = live_obj.name
                ctx['live_content'] = live_obj.description
                
            ctx['proposed_title'] = proposal.proposed_name
            ctx['proposed_content'] = proposal.proposed_description
            ctx['change_log'] = proposal.change_log
            if live_obj:
                ctx['live_version_number'] = live_obj.current_version_number
            
            # Calculate Diffs
            ctx['diff_title'] = get_diff_html(ctx['live_title'], ctx['proposed_title'])
            ctx['diff_content'] = get_diff_html(ctx['live_content'], ctx['proposed_content'])
            
        elif type == 'NARRATIVE':
            proposal = get_object_or_404(CaosNarrativeVersionORM, id=id)
            if proposal.narrative:
                live_obj = proposal.narrative
                ctx['live_title'] = live_obj.titulo
                ctx['live_content'] = live_obj.contenido
                
            ctx['proposed_title'] = proposal.proposed_title
            ctx['proposed_content'] = proposal.proposed_content
            ctx['change_log'] = proposal.change_log
            if live_obj:
                ctx['live_version_number'] = live_obj.current_version_number
            
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
            if type == 'WORLD': return redirect('aprobar_version', id=id)
            elif type == 'NARRATIVE': return redirect('aprobar_narrativa', id=id)
            elif type == 'IMAGE': return redirect('aprobar_imagen', id=id)
            
        elif action == 'reject':
            # DIRECT CALL to pass POST data (reason)
            if type == 'WORLD': return rechazar_propuesta(request, id=id)
            elif type == 'NARRATIVE': return rechazar_narrativa(request, id=id)
            elif type == 'IMAGE': return rechazar_imagen(request, id=id)

    ctx['proposal'] = proposal
    return render(request, 'staff/review_proposal.html', ctx)
