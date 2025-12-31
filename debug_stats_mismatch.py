
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosLike, CaosComment, CaosNarrativeORM
import json

def debug_stats():
    target_user = User.objects.get(id=2)
    print(f"DEBUG FOR USER: {target_user.username} (id: {target_user.id})")
    
    # 1. Check uploader field in gallery_log
    print("\n--- GALLERY LOG CHECK ---")
    worlds = CaosWorldORM.objects.filter(is_active=True)
    for world in worlds:
        if world.metadata and 'gallery_log' in world.metadata:
            log = world.metadata['gallery_log']
            for filename, meta in log.items():
                uploader = meta.get('uploader')
                if uploader and uploader.lower() == target_user.username.lower():
                    entity_key = f"IMG_{filename}"
                    likes = CaosLike.objects.filter(entity_key__iexact=entity_key).count()
                    comments = CaosComment.objects.filter(entity_key__iexact=entity_key).count()
                    print(f"Found image: {filename} in world {world.name}")
                    print(f"  - Uploader in meta: {uploader}")
                    print(f"  - Entity Key: {entity_key}")
                    print(f"  - DB Likes (iexact): {likes}")
                    print(f"  - DB Comments (iexact): {comments}")
                    
                    if likes == 0:
                        # Try to find ALL likes for this filename to see if there's a variation
                        all_likes = CaosLike.objects.filter(entity_key__icontains=filename)
                        if all_likes.exists():
                            print(f"  - WARNING: Found potential key mismatch. Exact key |{entity_key}| not found, but similar keys exist:")
                            for l in all_likes:
                                print(f"    * |{l.entity_key}|")

    # 2. Check Narratives
    print("\n--- NARRATIVES CHECK ---")
    narratives = CaosNarrativeORM.objects.filter(created_by=target_user, is_active=True)
    for n in narratives:
        entity_key = f"NARR_{n.public_id}"
        likes = CaosLike.objects.filter(entity_key__iexact=entity_key).count()
        print(f"Narrative: {n.titulo} ({n.public_id})")
        print(f"  - Likes: {likes}")

if __name__ == "__main__":
    debug_stats()
