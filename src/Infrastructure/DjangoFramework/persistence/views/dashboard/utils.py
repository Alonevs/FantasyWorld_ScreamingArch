from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from src.Infrastructure.DjangoFramework.persistence.models import CaosEventLog, CaosVersionORM, CaosNarrativeVersionORM, CaosImageProposalORM, TimelinePeriodVersion
from src.Infrastructure.DjangoFramework.persistence.policies import get_user_access_level

def get_visible_user_ids(user):
    """
    Returns a tuple (is_global, user_ids) determining what data a user can see.
    - is_global: True if user is Superuser/Superadmin (can see everything).
    - user_ids: List of IDs (Self + Minions) if restricted. Ignore if is_global is True.
    """
    # 1. Global Admins
    if user.is_superuser or (hasattr(user, 'profile') and user.profile.rank == 'SUPERADMIN'):
        return True, []

    # 2. Territorial Logic (Admins/Bosses see themselves + Minions)
    visible_ids = [user.id]
    if hasattr(user, 'profile'):
        # Collaborators (Minions)
        minion_ids = list(user.profile.collaborators.values_list('user__id', flat=True))
        visible_ids.extend(minion_ids)

    return False, visible_ids

def log_event(user, action, target_id, details=""):
    try:
        u = user if user.is_authenticated else None
        tid = str(target_id) if target_id else None
        CaosEventLog.objects.create(user=u, action=action, target_id=tid, details=details)
    except Exception as e: print(f"Log Error: {e}")

def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or (hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUBADMIN']))

def is_superuser(user): return user.is_superuser

def has_authority_over_proposal(user, obj):
    """
    Determina si un usuario tiene autoridad para aprobar/rechazar/borrar una propuesta.
    Un usuario tiene autoridad si:
    1. Es Superuser.
    2. Es el Autor del Mundo asociado (Boss).
    3. Es el Autor de la propuesta (Solo para BORRAR su propia propuesta).
    """
    if user.is_superuser: return True
    
    # Obtener el mundo asociado al objeto
    world = None
    if hasattr(obj, 'world'): world = obj.world
    elif hasattr(obj, 'narrative'): world = obj.narrative.world
    elif hasattr(obj, 'period'): world = obj.period.world
    
    if world:
        # Usar la política centralizada: OWNER o SUPERUSER tienen autoridad total.
        access = get_user_access_level(user, world)
        if access in ['OWNER', 'SUPERUSER']:
            return True
            
    # Caso especial: El autor de la propuesta puede borrar su propia propuesta PENDIENTE
    if hasattr(obj, 'author') and obj.author == user and obj.status == 'PENDING':
        return True
        
    return False

# --- GENERIC ACTION HELPERS ---

def execute_use_case_action(request, use_case_cls, id, success_msg, log_code, extra_args=None, skip_auth=False):
    """
    Executes a standard clean architecture Use Case.
    Assumes use_case_cls() constructor and execute(id) method.
    Automatically passes 'reviewer' if doing APPROVE/REJECT actions.
    """
    try:
        # SECURITY CHECK: Verify authority before executing Use Case
        # Assuming the model can be inferred or passed. 
        # For simplicity, we fetch the object first.
        # This is a bit redundant with UseCase internal fetch, but essential for security.
        # We need the class to fetch. Since use_case_cls doesn't give it easily, 
        # we assume current views pass the object already or we fetch it here.
        # REFACTOR: In this project, execute_use_case_action is called with the ID. 
        # We'll infer the model based on log_code.
        model_map = {
            'WORLD': CaosVersionORM,
            'NARRATIVE': CaosNarrativeVersionORM,
            'IMAGE': CaosImageProposalORM,
            'PERIOD': TimelinePeriodVersion
        }
        model_key = next((k for k in model_map if k in log_code), 'WORLD')
        target_model = model_map.get(model_key)
        
        obj = get_object_or_404(target_model, id=id)

        if not skip_auth:
            if not has_authority_over_proposal(request.user, obj):
                messages.error(request, "⛔ No tienes autoridad para realizar esta acción sobre este elemento.")
                return redirect('dashboard')
 
        use_case = use_case_cls()
        args = extra_args or {}
        
        # Auto-inject reviewer for traceability
        if "APPROVE" in log_code or "REJECT" in log_code or "PUBLISH" in log_code:
            args['reviewer'] = request.user
            
        if "RESTORE" in log_code:
            args['user'] = request.user

        res = use_case.execute(id, **args)
        
        # If UseCase returns a Proposal object (like Restore), redirect to it?
        # But standard behavior is redirect to dashboard/next.
        # We ignore return unless we need it.
             
        # SMART TOAST: If user is the author AND it's an Approval/Rejection (which generates Notification),
        # suppress the generic Toast to avoid double noise.
        is_self_review = hasattr(obj, 'author') and obj.author == request.user
        is_review_action = "APPROVE" in log_code or "REJECT" in log_code or "PUBLISH" in log_code
        
        should_show_toast = True
        if is_self_review and is_review_action:
            should_show_toast = False
            
        if should_show_toast and success_msg:
            messages.success(request, success_msg)
            
        log_event(request.user, log_code, id)
        
        # Return result in case caller needs it (e.g. new proposal ID)
        if res: return res 

    except Exception as e:
        messages.error(request, f"Error: {e}")
    
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')

def execute_orm_status_change(request, model_cls, id, status, success_msg, log_code=None):
    """
    Directly updates the status of an ORM object.
    """
    try:
        obj = get_object_or_404(model_cls, id=id)

        # SECURITY CHECK
        if not has_authority_over_proposal(request.user, obj):
            messages.error(request, "⛔ No tienes autoridad para modificar este elemento.")
            return redirect('dashboard')

        obj.status = status
        
        # Traceability: Set reviewer if field exists
        if hasattr(obj, 'reviewer'):
            obj.reviewer = request.user
            
        obj.save()
        messages.success(request, success_msg)
        if log_code: log_event(request.user, log_code, id)
    except Exception as e:
        messages.error(request, f"Error: {e}")
    
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')

def execute_orm_delete(request, model_cls, id, success_msg, log_code=None):
    try:
        obj = get_object_or_404(model_cls, id=id)

        # SECURITY CHECK
        if not has_authority_over_proposal(request.user, obj):
            messages.error(request, "⛔ No tienes autoridad para eliminar este elemento.")
            return redirect('dashboard')

        obj.delete()
        messages.success(request, success_msg)
        if log_code: log_event(request.user, log_code, id)
    except Exception as e:
        messages.error(request, f"Error: {e}")
    
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')
