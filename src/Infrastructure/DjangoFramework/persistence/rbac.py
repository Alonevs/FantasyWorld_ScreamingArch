from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import messages

# --- JERARQUÍA DE ROLES Y PESOS ---
"""
Define el sistema de permisos basado en rangos. 
Cuanto mayor es el valor numérico, mayor es la autoridad.
"""
ROLE_HIERARCHY = {
    'SUPERADMIN': 100,  # "Alone" - Acceso total y supervisión técnica global.
    'ADMIN': 50,        # "Boss" - Dueño de sus mundos y gestor de su equipo.
    'SUBADMIN': 20,     # "Colaborador" - Ayuda en mundos ajenos (solo visualiza borradores).
    'USER': 0,          # "Explorador" - Solo puede leer contenido público 'Live'.
    'EXPLORER': 0       # Alias heredado.
}

def get_user_rank_value(user) -> int:
    """
    Obtiene el peso numérico del rango del usuario actual.
    Si es Superuser de Django, se le asigna automáticamente el rango máximo.
    """
    if not user.is_authenticated:
        return -1
        
    if user.is_superuser:
        return ROLE_HIERARCHY['SUPERADMIN']
        
    if hasattr(user, 'profile'):
        rank_str = user.profile.rank.upper()
        # Retorna el peso del rango o 0 (Explorer) si no se reconoce.
        return ROLE_HIERARCHY.get(rank_str, 0)
        
    return 0 # Por defecto: Explorador

def check_role_access(user, min_role_name: str) -> bool:
    """
    Valida si el usuario cumple con el rango mínimo exigido.
    
    Args:
        user: El objeto User de Django.
        min_role_name: El nombre del rango requerido (ej: 'ADMIN').
    """
    user_val = get_user_rank_value(user)
    required_val = ROLE_HIERARCHY.get(min_role_name, 0)
    return user_val >= required_val

# --- DECORADORES DE VISTA (RBAC) ---

def requires_role(role_name: str):
    """
    Decorador maestro para denegar el acceso a vistas si no se cumple el rango.
    Redirige al dashboard/home con un mensaje de error estilizado.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not check_role_access(request.user, role_name):
                # Generar mensaje de sistema mediante CaosModal (vía messages)
                messages.error(request, f"⛔ Acceso Denegado. Se requiere rango {role_name} para realizar esta acción.")
                
                if request.user.is_authenticated:
                    return redirect('home')
                return redirect('login')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def restrict_explorer(view_func):
    """Acceso restringido: Solo para Colaboradores (SUBADMIN) o superiores."""
    return requires_role('SUBADMIN')(view_func)

def admin_only(view_func):
    """Acceso exclusivo para Administradores (ADMIN) y Superadmins."""
    return requires_role('ADMIN')(view_func)
