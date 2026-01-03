from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosEventLog
from ..utils import get_visible_user_ids

@login_required
def audit_log_view(request):
    """
    Vista detallada del Registro de Auditoría (Audit Log).
    Muestra todas las acciones registradas en el sistema (Global para Admins).
    Permite filtrar por Usuario, Tipo de Acción y Búsqueda de texto libre.
    """
    is_global, visible_ids = get_visible_user_ids(request.user)
    
    logs = CaosEventLog.objects.all().order_by('-timestamp')
    if not is_global:
        logs = logs.filter(user_id__in=visible_ids)

    # Allow filtering only by visible users for non-globals
    if is_global:
        users = User.objects.all().order_by('username')
    else:
        users = User.objects.filter(id__in=visible_ids).order_by('username')

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
