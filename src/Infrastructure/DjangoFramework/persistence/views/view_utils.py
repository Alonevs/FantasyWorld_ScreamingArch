from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id

def resolve_jid_orm(identifier) -> CaosWorldORM:
    """
    Resolves a J-ID or PublicID (NanoID) to a CaosWorldORM instance.
    Returns None if not found.
    """
    repo = DjangoCaosRepository()
    w_domain = resolve_world_id(repo, identifier)
    if w_domain:
        try:
            return CaosWorldORM.objects.get(id=w_domain.id.value)
        except CaosWorldORM.DoesNotExist:
            return None
            
    # Fallback: Try identifying as NanoID or ID directly
    try:
        # Try public_id (NanoID)
        return CaosWorldORM.objects.get(public_id=identifier)
    except CaosWorldORM.DoesNotExist:
        try:
            # Try plain ID (Integer)
            return CaosWorldORM.objects.get(id=identifier)
        except (CaosWorldORM.DoesNotExist, ValueError):
            return None
    return None

def check_world_access(request, world_orm: CaosWorldORM):
    """
    Checks if the current user has access to view a world.
    Rules: 
    1. Status 'LIVE' is public.
    2. Other statuses require:
       - Being the author
       - Being a collaborator of the author
       - Being a superuser
    Returns (can_access: bool, is_author_or_team: bool)
    """
    if not world_orm:
        return False, False

    is_live = (world_orm.status == 'LIVE')
    is_superuser = request.user.is_superuser
    is_authenticated = request.user.is_authenticated
    
    is_strict_author = (is_authenticated and world_orm.author == request.user)
    
    is_collaborator = False
    if is_authenticated and not is_strict_author:
        if world_orm.author and hasattr(world_orm.author, 'profile'):
            if request.user.profile in world_orm.author.profile.collaborators.all():
                is_collaborator = True

    
    # Check Profile Rank (Admin/SubAdmin)
    is_profile_admin = False
    if is_authenticated and hasattr(request.user, 'profile'):
        if request.user.profile.rank in ['ADMIN', 'SUBADMIN']:
            is_profile_admin = True

    is_author_or_team = is_strict_author or is_collaborator or is_superuser or is_profile_admin
    can_access = is_live or is_author_or_team
    
    return can_access, is_author_or_team

def get_admin_status(user):
    """Checks if the user has an ADMIN or SUBADMIN rank."""
    if not user.is_authenticated:
        return False, False
    
    try:
        rank = user.profile.rank
        return rank == 'ADMIN', rank in ['ADMIN', 'SUBADMIN']
    except:
        return False, False
