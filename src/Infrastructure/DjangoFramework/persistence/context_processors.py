from .rbac import get_user_rank_value

def rbac_context(request):
    """
    Injects 'user_role' integer value into every template context.
    SUPERADMIN = 100
    ADMIN = 50
    SUBADMIN = 20
    USER/EXPLORER = 0
    """
    return {
        'user_role': get_user_rank_value(request.user)
    }
