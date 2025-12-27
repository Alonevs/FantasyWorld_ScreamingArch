from django.core.exceptions import PermissionDenied

def check_ownership(user, obj):
    """
    Verifica si un usuario tiene jurisdicción legal sobre un objeto de contenido.
    Aplica las reglas de soberanía y colaboración definidas en readme_rules.md.
    
    Reglas de Acceso:
    1. Superusuario (Alone) -> Acceso Global.
    2. Autor/Creador -> Soberanía Total sobre su obra.
    3. Equipo de Colaboración (Boss/Minion) -> El Jefe puede editar lo del Subadmin
       y el Subadmin puede editar lo del Jefe si están vinculados en el perfil.
    """
    if not user.is_authenticated:
        raise PermissionDenied("Se requiere autenticación para realizar esta operación.")
        
    # 1. ACCESO GLOBAL (Superadmin)
    if user.is_superuser: 
        return True
         
    # 2. IDENTIFICACIÓN DEL PROPIETARIO
    owner = None
    if hasattr(obj, 'author'):
        owner = obj.author
    elif hasattr(obj, 'created_by'):
        owner = obj.created_by
        
    if owner:
        # Acceso directo por autoría
        if owner == user: 
            return True
        
        # 3. LÓGICA DE JURISDICCIÓN (Colaboración Boss/Minion)
        try:
            if hasattr(owner, 'profile') and hasattr(user, 'profile'):
                # Caso A: El usuario actual es un colaborador autorizado del propietario (Minion trabajando para Boss).
                if user.profile in owner.profile.collaborators.all():
                    return True
                
                # Caso B: El usuario es el Jefe (ADMIN) y el propietario es uno de sus colaboradores (Boss editando a Minion).
                if user.profile.rank == 'ADMIN':
                    if owner.profile in user.profile.collaborators.all():
                        return True
                    
                    # Caso C (FEDERADO): Admin puede ver contenido del Superadmin (para proponer).
                    # Esto desbloquea la vista de "Offline" del Superadmin para los Admins.
                    if owner.is_superuser:
                        return True

        except Exception:
            pass
            
    # Denegación por defecto si no se cumple ninguna jerarquía de poder.
    raise PermissionDenied("⛔ ACCESO DENEGADO: No tienes jurisdicción sobre este contenido.")
