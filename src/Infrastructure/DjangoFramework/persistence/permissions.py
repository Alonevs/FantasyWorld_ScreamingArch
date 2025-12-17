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
    if hasattr(obj, 'author') and obj.author == user:
        return True
        
    # Check for 'created_by' field (Narratives)
    if hasattr(obj, 'created_by') and obj.created_by == user:
        return True
        
    raise PermissionDenied("No tiene permiso para editar esta entidad.")
