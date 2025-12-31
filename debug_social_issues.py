import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosComment, CaosLike, CaosWorldORM, CaosVersionORM
from src.Shared.Services.SocialService import SocialService

def debug():
    print("--- DEBUGGING ROBERTO & ALONE SOCIAL ---")
    
    # 1. Users
    roberto = User.objects.filter(username__iexact='roberto').first()
    alone = User.objects.filter(id=2).first() # Alone
    
    if not roberto:
        print("Roberto not found!")
        # Try to find any user that is not alone or admin
        roberto = User.objects.exclude(username__in=['admin', 'Alone']).first()
        if roberto:
            print(f"Using alternative user: {roberto.username}")
    
    if not alone:
        print("Alone (ID 2) not found!")
        return

    print(f"Roberto: {roberto.username if roberto else 'N/A'} (ID: {roberto.id if roberto else 'N/A'})")
    print(f"Alone: {alone.username} (ID: {alone.id})")

    # 2. Comments from Roberto
    if roberto:
        print("\n--- Comments FROM Roberto ---")
        comments = CaosComment.objects.filter(user=roberto).order_by('-created_at')
        for c in comments:
            parent_link = f"REPLY to {c.parent_comment.id} (key: {c.parent_comment.entity_key})" if c.parent_comment else "TOP-LEVEL"
            print(f"ID: {c.id} | Key: {c.entity_key} | {parent_link} | Content: {c.content[:50]}")

    # 3. Comments ON Alone's content
    print("\n--- Discovery for Alone ---")
    content = SocialService.discover_user_content(alone)
    print(f"Worlds: {len(content['worlds'])}")
    print(f"Images: {len(content['images'])}")
    
    # Check all images found
    image_keys = [f"IMG_{img['filename']}" for img in content['images']]
    print(f"Image Entity Keys: {image_keys}")
    
    print("\n--- Comments received by Alone ---")
    # This logic matches what TeamView.get_context_data does (simplifed)
    received = []
    
    # A. Worlds
    for w in content['worlds']:
        key = f"WRLD_{w.public_id}"
        count = CaosComment.objects.filter(SocialService.get_robust_query(key)).count()
        if count > 0:
            print(f"World {w.name} has {count} comments")
    
    # B. Images
    for img in content['images']:
        key = f"IMG_{img['filename']}"
        q = SocialService.get_robust_query(key)
        comments = CaosComment.objects.filter(q).select_related('user')
        if comments.exists():
            print(f"Image {img['filename']} has {comments.count()} comments")
            for c in comments:
                print(f"  Comment by {c.user.username}: {c.content[:30]}")

    # 4. Check for orphaned comments and file ownership
    print("\n--- Checking Ownership of Files ---")
    files_to_trace = ['REALIDADES_V1.WEBP', 'Realidades_v1.webp', '00000-898820933.WEBP']
    
    for filename in files_to_trace:
        norm_filename = filename.lower().replace('\\u002d', '-').replace('\\u002D', '-')
        print(f"\nTracing '{filename}' (normalized: {norm_filename}):")
        
        worlds = CaosWorldORM.objects.filter(is_active=True)
        found = False
        for w in worlds:
            if not w.metadata: continue
            
            # Check gallery
            gallery = w.metadata.get('gallery_log', {})
            for g_file, g_meta in gallery.items():
                if g_file.lower().replace('\\u002d', '-').replace('\\u002D', '-') == norm_filename:
                    print(f"  FOUND in World '{w.name}' (ID {w.id}) Gallery. Uploader: '{g_meta.get('uploader')}'")
                    found = True
            
            # Check cover
            cover = w.metadata.get('cover_image', '')
            if cover.lower().replace('\\u002d', '-').replace('\\u002D', '-') == norm_filename:
                print(f"  FOUND as World '{w.name}' (ID {w.id}) COVER.")
                found = True
                
            # Check timeline
            timeline = w.metadata.get('timeline', {})
            for year, data in timeline.items():
                p_gallery = data.get('gallery_log', {})
                for p_file, p_meta in p_gallery.items():
                    if p_file.lower().replace('\\u002d', '-').replace('\\u002D', '-') == norm_filename:
                        print(f"    FOUND in World '{w.name}' Timeline {year} Gallery. Uploader: '{p_meta.get('uploader')}'")
                        found = True
        if not found:
            # Check TimelinePeriodVersion
            from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriodVersion
            p_versions = TimelinePeriodVersion.objects.filter(status='PENDING')
            for pv in p_versions:
                if pv.proposed_snapshot:
                    if norm_filename in str(pv.proposed_snapshot).lower():
                        print(f"    FOUND in TIMELINE PERIOD VERSION ID {pv.id} (Period: {pv.period.title})")
                        found = True

        if not found:
            # Check Event Log
            from src.Infrastructure.DjangoFramework.persistence.models import CaosEventLog
            logs = CaosEventLog.objects.filter(details__icontains=filename) | CaosEventLog.objects.filter(details__icontains=norm_filename)
            for l in logs:
                print(f"    FOUND EVENT LOG: {l.action} by {l.user.username} (Details: {l.details[:100]})")
                found = True
        
        if not found:
            print("  NOT FOUND in ANY metadata, history, versions or logs!")

if __name__ == "__main__":
    debug()
