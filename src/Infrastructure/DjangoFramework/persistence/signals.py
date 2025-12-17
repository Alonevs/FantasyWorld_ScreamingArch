from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

@receiver(pre_delete, sender=User)
def prevent_critical_user_deletion(sender, instance, **kwargs):
    """
    Prevents deletion of critical system users.
    'Xico' = AI/System user.
    'Alone' = Superadmin.
    """
    if instance.username in ['Xico', 'Alone']:
        raise PermissionDenied(f"CRITICAL ERROR: The user '{instance.username}' is PROTECTED and cannot be deleted.")
