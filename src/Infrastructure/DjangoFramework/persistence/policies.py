import logging
from django.db.models import Q
from .models import CaosWorldORM

# Security logger
security_logger = logging.getLogger('security')

def get_visibility_q_filter(user):
    """
    Retorna el objeto Q de Django que define QUÉ MUNDOS puede ver un usuario en la navegación general (Home/Lista).
    """
    # 1. Superuser: Ve todo (Dios)
    if not user.is_authenticated:
        return Q(status='LIVE', visible_publico=True)

    if user.is_superuser:
        return Q() # Todo
    
    # 2. Explorer / SubAdmin (Navigation mode): See only LIVE public or Bosses' LIVE.
    # The requirement says SubAdmin "solo ve las cosas live".
    # We allow them to see their Bosses' stuff but only if it's LIVE or if they are in the Detail view.
    # In Home/Search, stay public-centric for them.
    if hasattr(user, 'profile'):
        my_bosses_users = [bp.user for bp in user.profile.bosses.all()]
        
        if user.profile.rank == 'SUBADMIN':
            # Subadmin only sees LIVE (Public or Bosses')
            return Q(status='LIVE') & (Q(visible_publico=True) | Q(author__in=my_bosses_users))
        
        if user.profile.rank == 'ADMIN':
            # Admin sees his stuff, his bosses' stuff (Admin collaboration), and system worlds.
            # "Un admin colabora con otro admin ven y pueden proponer de otros admins"
            # This is covered by 'author__in=my_bosses_users' (Bosses include Admin collaborators).
            # They also see their Minions' stuff.
            my_minion_users = [cp.user for cp in user.profile.collaborators.all()]
            
            return Q(author=user) | Q(author__in=my_bosses_users) | Q(author__in=my_minion_users) | \
                   Q(status='LIVE', visible_publico=True) | Q(author__is_superuser=True) | Q(author__isnull=True)

    return Q(status='LIVE', visible_publico=True)

def get_user_access_level(user, world):
    """
    Retorna el nivel de acceso del usuario sobre un mundo específico.
    """
    if not user.is_authenticated: return 'NONE'
    if user.is_superuser: return 'SUPERUSER'
    if world.author == user: return 'OWNER'
    
    if hasattr(user, 'profile') and hasattr(world.author, 'profile'):
        # Minion -> Boss (Covers SubAdmin -> Admin and Admin -> Admin collab)
        if user.profile.bosses.filter(user=world.author).exists(): return 'COLLABORATOR'
        
        # Boss -> Minion (Admin sees his team's drafts)
        if user.profile.rank == 'ADMIN' and user.profile.collaborators.filter(user=world.author).exists():
            return 'COLLABORATOR'
        
    return 'NONE'

def can_user_propose_on(user, world):
    """
    Define si un usuario puede VER LOS BOTONES de edición y proponer cambios.
    """
    access = get_user_access_level(user, world)
    
    if access in ['SUPERUSER', 'OWNER', 'COLLABORATOR']:
        return True
        
    # Los Administradores (ADMIN) pueden proponer en mundos del SISTEMA (Superuser)
    if hasattr(user, 'profile') and user.profile.rank == 'ADMIN':
        if not world.author or world.author.is_superuser:
            return True
            
    return False

def can_user_view_world(user, world):
    """
    Determina si un usuario tiene permiso para entrar en la ficha de un mundo.
    """
    if world.status == 'LIVE' and world.visible_publico:
        return True
        
    if not user.is_authenticated: return False
    
    # Superuser ve todo
    if user.is_superuser: return True

    # Nivel de acceso directo (Owner o Colaborador)
    access = get_user_access_level(user, world)
    if access in ['OWNER', 'COLLABORATOR']:
        # Exception for Subadmin: They only see their Boss's stuff if they are collaborators.
        # But if the world is DRAFT/OFFLINE, and user is SUBADMIN? 
        # User said: "subadmin... solo ve las cosas live". 
        # However, they need to see it to edit it? Usually, "edit" is on LIVE to create a VERSION.
        # If the WORLD ITSELF IS OFFLINE/DRAFT, Subadmins shouldn't see it (only Admins/Super).
        if hasattr(user, 'profile') and user.profile.rank == 'SUBADMIN':
            return world.status == 'LIVE'
        return True

    # Federación para Admins (Ver mundos de Superuser para proponer)
    if hasattr(user, 'profile') and user.profile.rank == 'ADMIN':
        if not world.author or world.author.is_superuser:
            return True

    return False

def can_user_delete_request(user, world):
    """
    Define si un usuario puede solicitar borrado.
    Mismas reglas que proponer (ya que borrar ES una propuesta).
    """
    return can_user_propose_on(user, world)
