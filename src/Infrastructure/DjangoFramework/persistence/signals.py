from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

@receiver(pre_delete, sender=User)
def prevent_critical_user_deletion(sender, instance, **kwargs):
    """
    Señal de seguridad para proteger cuentas críticas del sistema.
    Evita la eliminación accidental o malintencionada de usuarios pilares.
    
    Protegidos:
    - 'Xico': Identidad de la IA / System User.
    - 'Alone': Identidad del Superadministrador Global.
    """
    nombres_protegidos = ['Xico', 'Alone']
    
    if instance.username in nombres_protegidos:
        raise PermissionDenied(
            f"⛔ ERROR CRÍTICO: El usuario '{instance.username}' está PROTEGIDO por el núcleo del sistema y su eliminación está prohibida."
        )
