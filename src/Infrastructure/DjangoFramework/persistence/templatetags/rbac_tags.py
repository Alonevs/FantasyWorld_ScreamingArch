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
            # But wait, item.author might be 'Alone'. If 'Alone' proposes on my world, I can approve (I am Owner).
            # If 'Alone' proposes on HIS world, I (Pepe) cannot approve.
            # So 'can_publish' covers Owner case.
            
            # What if I am Collaborator on Alone's world?
            # User says: "El botón... OCULTOS para el autor... si no es el Dueño o Superadmin."
            # "Un Admin NO puede auto-aprobar sus cambios en un mundo que pertenece a otro".
            # What about approving OTHER's changes?
            # "Solo el Dueño... o Superadmin... pueden ver... PUBLICAR".
            # Logic for APPROVE (Draft -> Ready) is distinct from PUBLISH (Ready -> Live).
            # Usually Collaborators can Approve others' work?
            # User didn't explicitly forbid Collaborators from Approving OTHERS.
            # "El botón de 'APROBAR'... ocultos para el autor...". (Implies valid for non-author).
            # But "Un Admin NO puede auto-aprobar...".
            
            # Let's be strict: Only Owner/Superadmin can Approve too?
            # No, "Distinción crítica: Permitir crear propuestas... Mantener que solo dueño... PUBLICAR".
            # So Creation is allowed. Approval?
            # If logic is Create -> Pending -> Approve -> Approved -> Publish -> Live.
            # If Collaborator creates Pending. Who Approves? Owner.
            # Can Collaborator Approve Owner's proposal? Probably not.
            # Can Collaborator A Approve Collaborator B? Maybe.
            
            # SAFEST BET: Only Owner/Superadmin/Boss can Approve.
            # Collaborators can PROPOSE (Create).
            
            # Check if Item Author is my minion (I am their Boss)
            if hasattr(item.author, 'profile'):
                if item.author.profile in user.profile.collaborators.all():
                    return True
                    
    except: pass
        
    return False
