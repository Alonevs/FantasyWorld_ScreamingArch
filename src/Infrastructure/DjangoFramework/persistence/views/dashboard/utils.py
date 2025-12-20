from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from src.Infrastructure.DjangoFramework.persistence.models import CaosEventLog

def log_event(user, action, target_id, details=""):
    try:
        u = user if user.is_authenticated else None
        tid = str(target_id) if target_id else None
        CaosEventLog.objects.create(user=u, action=action, target_id=tid, details=details)
    except Exception as e: print(f"Log Error: {e}")

def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or (hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUBADMIN']))

def is_superuser(user): return user.is_superuser

# --- GENERIC ACTION HELPERS ---

def execute_use_case_action(request, use_case_cls, id, success_msg, log_code, extra_args=None):
    """
    Executes a standard clean architecture Use Case.
    Assumes use_case_cls() constructor and execute(id) method unless extra_args provided.
    """
    try:
        use_case = use_case_cls()
        if extra_args:
             use_case.execute(id, **extra_args)
        else:
             use_case.execute(id)
             
        messages.success(request, success_msg)
        log_event(request.user, log_code, id)
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
        obj.status = status
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
        obj.delete()
        messages.success(request, success_msg)
        if log_code: log_event(request.user, log_code, id)
    except Exception as e:
        messages.error(request, f"Error: {e}")
    
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url) if next_url else redirect('dashboard')
