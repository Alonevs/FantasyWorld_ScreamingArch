from django.core.exceptions import PermissionDenied

def check_ownership(user, obj):
    """
    Verifies if user has jurisdiction over the object.
    Rules:
    1. Superuser / Rank 100 -> YES.
    2. Author/Creator -> YES.
    3. Collaborator (User is in Author's team) -> YES.
    """
    if not user.is_authenticated:
        raise PermissionDenied("Debe iniciar sesión.")
        
    # 1. GLOBAL ACCESS
    if user.is_superuser: return True
    
    # Check Rank 100 via logic
    try:
        # Global Access for High Ranks
        if user.profile.rank in ['SUPERADMIN', 'ADMIN', 'SUBADMIN']: return True
    except: pass
        
    # 2. AUTHORSHIP
    owner = None
    if hasattr(obj, 'author'):
        owner = obj.author
    elif hasattr(obj, 'created_by'):
        owner = obj.created_by
        
    if owner:
        if owner == user: return True
        
        # 3. COLLABORATION (JURISDICTION)
        # "Is 'user' a collaborator of 'owner'?"
        # Owner's profile has a list of collaborators.
        try:
            if hasattr(owner, 'profile'):
                # Check if user is in the owner's collaborators list
                if user.profile in owner.profile.collaborators.all():
                    return True
                
                # REVERSE: If I am an Admin, and the owner is in my 'collaborators', I can edit their stuff?
                # "Admin (Pepe)... Own Worlds + Team".
                # If Pepe is Boss, and Owner is Minion.
                # Minion is in Pepe.collaborators.
                # So if owner.profile in user.profile.collaborators.all() -> YES.
                if hasattr(user, 'profile') and user.profile.rank == 'ADMIN':
                    if owner.profile in user.profile.collaborators.all():
                        return True
        except Exception as e:
            # print(f"Jurisdiction Check Error: {e}") 
            pass
            
    # Default Deny
    raise PermissionDenied("⛔ ACCESO DENEGADO: No tienes jurisdicción sobre este contenido.")
