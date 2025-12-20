from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import messages

# ROLE CONSTANTS AND WEIGHTS
ROLE_HIERARCHY = {
    'SUPERADMIN': 100,  # "Alone" - Global Access
    'ADMIN': 50,        # "Pepe" - Own Worlds + Team
    'SUBADMIN': 20,     # Collaborator - Drafts Only
    'USER': 0,          # Explorer - Read Only
    'EXPLORER': 0       # Alias
}

def get_user_rank_value(user):
    """Returns integer value of user rank."""
    if not user.is_authenticated:
        return -1
        
    if user.is_superuser:
        return ROLE_HIERARCHY['SUPERADMIN']
        
    if hasattr(user, 'profile'):
        rank_str = user.profile.rank.upper()
        # Fallback for old data or mismatches
        return ROLE_HIERARCHY.get(rank_str, 0)
        
    return 0 # Default User

def check_role_access(user, min_role_name):
    """
    Checks if user meets the minimum role requirement.
    """
    user_val = get_user_rank_value(user)
    required_val = ROLE_HIERARCHY.get(min_role_name, 0)
    return user_val >= required_val

# DECORATORS

def requires_role(role_name):
    """
    View decorator that denies access if user doesn't meet role.
    Redirects to dashboard with error or raises 403.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not check_role_access(request.user, role_name):
                # If it's an AJAX request or critical, maybe 403?
                # For UX, flash message and redirect to safe place
                messages.error(request, f"⛔ Acceso Denegado. Requiere rango {role_name}.")
                # If user is Explorer, maybe redirect home?
                if request.user.is_authenticated:
                    return redirect('home')
                return redirect('login')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def restrict_explorer(view_func):
    """Shortcut for requiring at least SUBADMIN (Contributor) access."""
    return requires_role('SUBADMIN')(view_func)

def admin_only(view_func):
    """Shortcut for ADMIN only."""
    return requires_role('ADMIN')(view_func)
