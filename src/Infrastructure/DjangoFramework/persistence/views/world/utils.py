"""
Utilidades internas para vistas de mundos.
"""
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosEventLog


def log_event(user, action, target_id, details=""):
    """
    Registra eventos de auditoría en la base de datos (CaosEventLog).
    Sirve para rastrear quién hizo qué y sobre qué entidad.
    """
    try:
        u = user if user.is_authenticated else None
        CaosEventLog.objects.create(user=u, action=action, target_id=target_id, details=details)
    except Exception as e: 
        print(f"Error al registrar evento: {e}")

def get_current_user(request):
    if request.user.is_authenticated: return request.user
    u, _ = User.objects.get_or_create(username='Admin')
    return u
