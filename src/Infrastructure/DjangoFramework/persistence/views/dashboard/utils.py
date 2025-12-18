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
