from django import template
from src.Infrastructure.DjangoFramework.persistence.models import UserProfile

register = template.Library()

@register.filter
def can_publish(user, item):
    """
    Returns True only if user is Superuser or Owner of the item's world.
    Collaborators (even Admins) cannot publish to Live.
    """
    if not user.is_authenticated: return False
    if user.is_superuser: return True
    
    # Check Rank 100 via profile
    try:
        if user.profile.rank == 'SUPERADMIN': return True
    except: pass

    # Get World Author
    world_author = None
    
    # Parse Item Type (CaosVersionORM or similar)
    # Item usually has .world attribute
    if hasattr(item, 'world') and item.world:
        if hasattr(item.world, 'author'):
            world_author = item.world.author
    
    # If no world/author found, deny (except superuser checked above)
    if not world_author: return False
    
    # STRICT CHECK: Only Owner
    return user == world_author

@register.filter
def can_approve(user, item):
    """
    Returns True if user can approve the item (move to Approved/Staging).
    Rules:
    1. User != Item Author (No Self-Approval).
    2. User is Superuser OR Owner OR Boss of Author.
    """
    if not user.is_authenticated: return False
    
    # 1. PERMISSIO RELAX: Superusers can approve anything.
    if user.is_superuser: return True

    # 2. OWNER RELAX: If I am the owner of the world, I can approve anything (including my own changes).
    if can_publish(user, item): return True

    # 3. NO SELF APPROVAL for non-owners (Collaborators/Admins on others' worlds)
    if hasattr(item, 'author') and item.author == user:
        return False
    
    # If I am Admin (Boss) and Author is my minion?
    try:
        if user.profile.rank == 'ADMIN':
            # Check if Item Author is in my 'collaborators' (I am their boss)
            
            # CASE: ADMIN SELF-APPROVAL (AUTONOMY)
            # If I am ADMIN and I Own the world, I can approve my own proposals (e.g. creating a new world feature).
            # This is "Self-Management" for Bosses.
            if hasattr(item, 'author') and item.author == user and can_publish(user, item):
                return True

            if hasattr(item.author, 'profile'):
                if item.author.profile in user.profile.collaborators.all():
                    return True
                    
    except: pass
        
    return False
