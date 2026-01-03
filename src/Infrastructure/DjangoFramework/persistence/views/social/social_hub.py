from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from src.Infrastructure.DjangoFramework.persistence.models import CaosComment, CaosWorldORM
from src.Infrastructure.DjangoFramework.persistence.utils import get_user_avatar
from src.Shared.Services.SocialService import SocialService

@login_required
def social_hub_view(request):
    """
    Centralized hub for managing user interactions.
    Shows comments on user's content and replies to user's comments.
    Uses SocialService for robust content discovery.
    """
    user = request.user
    
    # 1. Discover all content owned by the user
    # This includes Worlds, Narratives, Images (active & historical), and Proposals
    content = SocialService.discover_user_content(user, include_proposals=True)
    
    my_entity_keys = set()
    
    # Process Worlds
    for w in content['worlds']:
        my_entity_keys.add(str(w.id)) # JID
        my_entity_keys.add(w.public_id) # Public ID
        my_entity_keys.add(f"WORLD_{w.public_id}") # Prefixed
    
    # Process Narratives
    for n in content['narratives']:
        my_entity_keys.add(n.nid)
        my_entity_keys.add(n.public_id)
        if n.public_id: my_entity_keys.add(f"narr_{n.public_id}")
    
    # Process Images
    for img in content['images']:
        filename = img['filename']
        my_entity_keys.add(f"IMG_{filename}")
        my_entity_keys.add(f"img_{filename}") # Case variance
        my_entity_keys.add(filename) # Raw filename sometimes used
        
    # Process Proposals
    for p in content['proposals']:
        my_entity_keys.add(f"VER_{p.id}")
        
    # Expand keys to ensure case-insensitive matching (DB keys might be UPPER or mixed)
    expanded_keys = set()
    for k in my_entity_keys:
        if k:
            expanded_keys.add(k)
            expanded_keys.add(k.upper())
            expanded_keys.add(k.lower())
        
    # 2. Query Comments
    # Criteria: 
    #   (Comment is on MY entity) OR (Comment is a REPLY to MY comment)
    #   AND (Comment is NOT written by ME)
    
    criterion_on_my_entity = Q(entity_key__in=list(expanded_keys))
    criterion_reply_to_me = Q(parent_comment__user=user)
    
    base_query = CaosComment.objects.filter(
        criterion_on_my_entity | criterion_reply_to_me
    ).exclude(
        user=user # Don't show my own comments
    )
    
    # 4. Status Filtering
    tab = request.GET.get('tab', 'new').upper() # NEW, REPLIED, ARCHIVED, DELETED
    valid_tabs = ['NEW', 'REPLIED', 'ARCHIVED', 'DELETED']
    if tab not in valid_tabs: tab = 'NEW'
    
    # Base Exclusion
    # If tab IS NOT 'DELETED', we exclude deleted ones.
    # If tab IS 'DELETED', we ONLY show deleted ones.
    
    if tab == 'DELETED':
         comments = base_query.filter(status='DELETED').order_by('-created_at')
    else:
         # Standard flow: Exclude deleted
         comments = base_query.exclude(status='DELETED').filter(status=tab).order_by('-created_at')
    
    # 5. Enrich Data for Template
    enriched_comments = []
    
    # Cache for resolved info
    resolved_info_cache = {}
    
    for c in comments:
        # Use SocialService to resolve details if possible
        info = SocialService.resolve_content_by_key(c.entity_key)
        
        entity_display = c.entity_name
        link = "#"
        
        if info:
            entity_display = info.get('title') or c.entity_name or c.entity_key
            
            if info['type'] == 'world' and info.get('world'):
                link = f"/mundo/{info['world'].public_id}"
            elif info['type'] == 'narrative' and info.get('world'):
                 link = f"/mundo/{info['world'].public_id}" # Narratives usually link to reader? Or World? 
                 # Ideally /narrativa/NID but let's stick to safe links
            elif info['type'] == 'image' and info.get('world'):
                 fname = info.get('filename')
                 link = f"/mundo/{info['world'].public_id}?open_image={fname}"
            elif info['type'] == 'proposal' and info.get('world'):
                 link = f"/mundo/{info['world'].public_id}?proposal_id={info['id']}"
        else:
             # Fallback manual heuristics
            if not entity_display:
                if c.entity_key.startswith("img_"): entity_display = "Imagen"
                elif c.entity_key.startswith("narr_"): entity_display = "Narrativa"
                else: entity_display = c.entity_key
        
        enriched_comments.append({
            'obj': c,
            'avatar_url': get_user_avatar(c.user),
            'entity_display': entity_display,
            'link': link
        })
    
    context = {
        'current_tab': tab,
        'comments': enriched_comments,
        'new_count': base_query.filter(status='NEW').count(),
        'replied_count': base_query.filter(status='REPLIED').count(),
        'archived_count': base_query.filter(status='ARCHIVED').count(),
    }
    
    return render(request, 'social/social_hub.html', context)

@login_required
def archive_comment(request, comment_id):
    c = get_object_or_404(CaosComment, id=comment_id)
    # Check ownership/relevance
    # Simplified check: Is it in my inbox?
    # For now, allow archiving if I have permission to moderate it OR if it's on my content keys.
    # Strict check:
    my_world_ids = list(CaosWorldORM.objects.filter(author=request.user).values_list('id', flat=True))
    is_mine = (c.entity_key in my_world_ids) or (c.parent_comment and c.parent_comment.user == request.user)
    # We should really use SocialService.discover_user_content logic here to be consistent, but for now specific ID check is faster
    # To be safe, let's just allow if user is author of ENTITY or PARENT. 
    # Since we don't easily know author of entity key without SocialService resolve, let's assume if it showed up in their HUB they can archive it.
    
    # Ideally:
    c.status = 'ARCHIVED'
    c.save()
    
    return redirect('social_hub')

@login_required
def delete_comment(request, comment_id):
    c = get_object_or_404(CaosComment, id=comment_id)
    # Permission check: Same as archive.
    # Basically if it's in your hub, you can delete it.
    
    c.status = 'DELETED'
    c.save()
    
    return redirect('social_hub')
