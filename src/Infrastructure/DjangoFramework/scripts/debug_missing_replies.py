
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosComment, CaosWorldORM
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

def check_missing_replies():
    print("--- CHECKING COMMENTS FOR 'Alone' (User ID: ?) ---")
    # Assuming the current user is 'Alone' or we need to find them.
    # The user mentioned "Alone", implies the user 'xico0' might be 'Alone' or acting as them.
    # Let's search for comments involving 'Maria' or 'Roberto' content or authors.
    
    comments = CaosComment.objects.all().order_by('-created_at')[:50]
    
    print(f"\nScanning last 50 comments...")
    found_any = False
    for c in comments:
        replies_count = c.replies.count()
        if "Maria" in str(c.content) or "Maria" in str(c.user.username) or \
           "Roberto" in str(c.content) or "Roberto" in str(c.user.username):
            print(f"\n[MATCH FOUND]")
            print(f"ID: {c.id}")
            print(f"User: {c.user.username}")
            print(f"Content: {c.content}")
            print(f"Status: {c.status}")
            print(f"Replies (Count): {replies_count}")
            print(f"Entity Key: {c.entity_key}")
            
            for r in c.replies.all():
                print(f"  -> Reply by {r.user.username}: {r.content[:50]}...")
            
            found_any = True

    if not found_any:
        print("\nNo specific 'Maria' or 'Roberto' comments found in recent history.")

if __name__ == "__main__":
    check_missing_replies()
