
import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosComment

def fix_statuses():
    print("--- FIXING COMMENT STATUSES ---")
    
    # Find comments that have replies but are marked as NEW
    comments_to_fix = CaosComment.objects.annotate(
        real_reply_count=Count('replies')
    ).filter(
        real_reply_count__gt=0,
        status='NEW'
    )
    
    count = comments_to_fix.count()
    print(f"Found {count} comments with replies but status='NEW'.")
    
    if count > 0:
        for c in comments_to_fix:
            print(f"Fixing Comment ID {c.id} (User: {c.user.username}, Replies: {c.real_reply_count})")
            c.status = 'REPLIED'
            c.save()
        print("Done! logic inconsistency resolved.")
    else:
        print("No inconsistent comments found.")

if __name__ == "__main__":
    fix_statuses()
