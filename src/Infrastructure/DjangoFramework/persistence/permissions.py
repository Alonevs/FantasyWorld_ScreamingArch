from django.core.exceptions import PermissionDenied

def check_ownership(user, obj):
    """
    Verifies if user is superuser or author of the object.
    Raises PermissionDenied if not.
    """
    if not user.is_authenticated:
        raise PermissionDenied("Debe iniciar sesión.")
        
    if user.is_superuser:
        return True
        
    # Check for 'author' field
    if hasattr(obj, 'author'):
        if obj.author == user: return True
        # SUBADMIN CHECK: Edit Boss's stuff
        try:
            if hasattr(user, 'profile') and user.profile.boss == obj.author:
                return True
        except: pass

    # Check for 'created_by' field (Narratives)
    if hasattr(obj, 'created_by'):
        if obj.created_by == user: return True
        # SUBADMIN CHECK
        try:
            if hasattr(user, 'profile') and user.profile.boss == obj.created_by:
                return True
        except: pass
        
    raise PermissionDenied("No tiene permiso para editar esta entidad.")
