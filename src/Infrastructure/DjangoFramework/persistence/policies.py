import logging
from django.db.models import Q
from .models import CaosWorldORM

# Security logger
security_logger = logging.getLogger('security')

def get_visibility_q_filter(user):
    """
    Retorna el objeto Q de Django que define QUÉ MUNDOS puede ver un usuario.
    Centraliza la lógica de 'Silos', 'Federación' y 'Privacidad'.
    
    Usado en:
    - world_views.py (Home)
    - get_world_details.py (Descendientes)
    - dashboard (workflow.py)
    """
    # 1. Superuser: Ve todo (Dios)
    if not user.is_authenticated:
        # Anónimo: Solo LIVE y Público
        return Q(status='LIVE', visible_publico=True)

    if user.is_superuser:
        return Q() # Todo
    
    # 1.5. Explorer: Ve igual que anónimo (solo LIVE público)
    # Diferencia con anónimo: Explorer podrá puntuar mundos (futuro)
    if hasattr(user, 'profile') and user.profile.rank == 'EXPLORER':
        security_logger.debug(f"Explorer {user.username} accessing with public-only filter")
        return Q(status='LIVE', visible_publico=True)

    # 2. Definir 'Jefes' (Para SubAdmins)
    my_bosses_users = []
    is_admin_rank = False
    
    if hasattr(user, 'profile'):
        my_bosses_users = [bp.user for bp in user.profile.bosses.all()]
        if user.profile.rank in ['ADMIN', 'SUPERADMIN']:
            is_admin_rank = True
    
    # Fallback: Staff users are trusted as Admins for visibility scope
    if user.is_staff:
        is_admin_rank = True

    # 3. Construcción del Filtro Federado
    # Base: Público + Mío + Jefes
    q_filter = Q(status='LIVE', visible_publico=True) | Q(author=user) | Q(author__in=my_bosses_users)
    
    # Regla: Admin ve 'Sistema' (Superuser + Huérfanos) para proponer
    if is_admin_rank:
        q_filter |= Q(author__is_superuser=True)
        q_filter |= Q(author__isnull=True) # Incluir mundos sin autor (Legacy/System)

    return q_filter

def can_user_propose_on(user, world):
    """
    Define si un usuario puede PROPONER cambios y ver botones de edición.
    Regla: No interferencia entre Admins (Silos).
    """
    if not user.is_authenticated:
        return False
        
    if user.is_superuser: 
        return True # Superuser hace lo que quiera
        
    # Owner always can
    if world.author == user:
        return True
        
    # SubAdmin en equipo del Owner
    if hasattr(user, 'profile') and hasattr(world.author, 'profile'):
         if user.profile.bosses.filter(user=world.author).exists():
             return True

    # Admin en mundo del Superuser/Sistema
    if hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUPERADMIN']:
        # Si es del Superuser o Huérfano
        if not world.author or world.author.is_superuser:
            return True
            
    return False

def can_user_view_world(user, world):
    """
    Determina si un usuario tiene permiso estricto para ver un mundo específico.
    Debe reflejar la misma lógica que get_visibility_q_filter y check_world_access.
    """
    if not world: 
        return False
    
    # 1. Público y LIVE
    if world.status == 'LIVE' and world.visible_publico:
        return True
        
    if not user.is_authenticated:
        security_logger.debug(f"Anonymous user denied access to world {world.id} (not public)")
        return False
    
    # 2. Explorer: Solo ve LIVE público (igual que anónimo)
    if hasattr(user, 'profile') and user.profile.rank == 'EXPLORER':
        result = (world.status == 'LIVE' and world.visible_publico)
        if not result:
            security_logger.info(f"Explorer {user.username} denied access to non-public world {world.id}")
        return result
        
    # 3. Superuser
    if user.is_superuser:
        return True
        
    # 4. Propio
    if world.author == user:
        return True
        
    # 5. Colaboración (Boss/Minion)
    if hasattr(user, 'profile') and hasattr(world.author, 'profile'):
        # Caso A: Soy colaborador del autor (Minion ve al Boss)
        # Nota: La lógica dice "El Jefe puede editar lo del Subadmin...". 
        # Pero visibilidad federada dice "SubAdmins solo ven de sus Jefes".
        if user.profile.bosses.filter(user=world.author).exists():
            return True
        # Caso B: Soy Jefe y veo al Minion
        if user.profile.rank == 'ADMIN':
             if world.author.profile.bosses.filter(user=user).exists(): # world.author tiene de jefe a user
                 return True

    # 6. Regla Admin -> Superuser (Para proponer)
    if hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUPERADMIN']:
        if not world.author or world.author.is_superuser:
            return True
    
    # Access denied - log for security audit
    security_logger.warning(
        f"Access denied: {user.username} (rank: {user.profile.rank if hasattr(user, 'profile') else 'N/A'}) "
        f"attempted to access world {world.id} (status: {world.status}, public: {world.visible_publico}, "
        f"author: {world.author.username if world.author else 'None'})"
    )
    return False

def can_user_delete_request(user, world):
    """
    Define si un usuario puede solicitar borrado.
    Mismas reglas que proponer (ya que borrar ES una propuesta).
    """
    return can_user_propose_on(user, world)
