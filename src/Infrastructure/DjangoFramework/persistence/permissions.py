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
         
    # 2. CENTRALIZACIÓN DE POLÍTICAS
    from src.Infrastructure.DjangoFramework.persistence.policies import get_user_access_level
    access = get_user_access_level(user, obj)
    
    if access in ['OWNER', 'COLLABORATOR', 'SUPERUSER']:
        return True
            
    # Denegación por defecto si no se cumple ninguna jerarquía de poder.
    raise PermissionDenied("⛔ ACCESO DENEGADO: No tienes jurisdicción sobre este contenido.")
