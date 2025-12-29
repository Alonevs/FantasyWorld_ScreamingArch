import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, UserProfile
from src.Infrastructure.DjangoFramework.persistence.policies import get_visibility_q_filter
from django.contrib.auth.models import User

def debug_world(public_id):
    try:
        m = CaosWorldORM.objects.get(public_id=public_id)
        print(f"World: {m.name}")
        print(f"Status: {m.status}")
        print(f"Visible Publico: {m.visible_publico}")
        print(f"Author: {m.author.username}")
        
        # Check current user (mocking the subadmin)
        # Assuming the user is a subadmin, let's see why it would appear in the filter
        # I need to know which user the USER is logged in as.
        # But for now, let's see how the general filter behaves.
        
        # Test 1: Anonymous visibility
        print("\n--- Testing Anonymous Visibility ---")
        q_anon = get_visibility_q_filter(None)
        is_visible_anon = CaosWorldORM.objects.filter(q_anon, public_id=public_id).exists()
        print(f"Visible for Anonymous? {is_visible_anon}")
        
        # Test 2: Subadmin visibility (general)
        # We need a user with rank 10
        subadmins = User.objects.filter(profile__rank=10)
        if subadmins:
            sub = subadmins[0]
            print(f"\n--- Testing Subadmin Visibility (User: {sub.username}) ---")
            q_sub = get_visibility_q_filter(sub)
            is_visible_sub = CaosWorldORM.objects.filter(q_sub, public_id=public_id).exists()
            print(f"Visible for this Subadmin? {is_visible_sub}")
            
            # Check relation to author
            has_boss_relation = sub.profile.collaborators.filter(id=m.author.profile.id).exists()
            print(f"Is author ({m.author.username}) a boss of {sub.username}? {has_boss_relation}")
        else:
            print("\nNo Subadmin user found in DB to test.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    debug_world('D2Ri3fgDW4')
