
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosLike, CaosComment, CaosNarrativeORM
import json

def debug_existence():
    # 1. Get all unique entity keys with likes/comments
    like_keys = set(CaosLike.objects.values_list('entity_key', flat=True))
    comm_keys = set(CaosComment.objects.values_list('entity_key', flat=True))
    all_keys = like_keys.union(comm_keys)
    
    print(f"Total entries with social interactions: {len(all_keys)}")
    
    # 2. For each key, if it starts with IMG_, try to find the world/uploader
    for key in sorted(all_keys):
        if key.startswith("IMG_"):
            filename = key[4:] # remove IMG_
            # Also handle the escaped version if it exists
            # Actually filename in DB might have the escapes
            
            print(f"\nAnalyzing Key: {key}")
            likes = CaosLike.objects.filter(entity_key__iexact=key).count()
            comms = CaosComment.objects.filter(entity_key__iexact=key).count()
            print(f"  Social: {likes} likes, {comms} comments")
            
            found = False
            for world in CaosWorldORM.objects.filter(is_active=True):
                if world.metadata and 'gallery_log' in world.metadata:
                    log = world.metadata['gallery_log']
                    # Look for filename in log keys (using iexact logic for key matching)
                    match_filename = None
                    for log_filename in log.keys():
                        if log_filename.lower() == filename.lower():
                            match_filename = log_filename
                            break
                    
                    if match_filename:
                        meta = log[match_filename]
                        uploader = meta.get('uploader', 'Unknown')
                        print(f"  FOUND in World: {world.name} ({world.public_id})")
                        print(f"  Uploader: {uploader}")
                        found = True
            
            if not found:
                print("  ERROR: Image not found in any gallery_log")

if __name__ == "__main__":
    debug_existence()
