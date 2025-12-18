import os
import django
import sys

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import UserProfile

def reset_alone_role():
    try:
        u = User.objects.get(username='Alone')
        print(f"Initial State - Username: {u.username}")
        
        if not hasattr(u, 'profile'):
            print("Creating profile...")
            UserProfile.objects.create(user=u)
            u.refresh_from_db()

        print(f"Current Rank: {u.profile.rank}")
        
        # FORCE RESET to SUPERADMIN (which in our logic is implied by is_superuser but we set rank too for consistency)
        # Actually our RBAC logic: if user.is_superuser return 100.
        # But let's set rank to 'ADMIN' or ensure no conflicting data.
        # User requested: "Force the field 'role' or 'rank' to max value".
        # Model choices are ADMIN, SUBADMIN, USER.
        # 'SUPERADMIN' isn't a choice in model, but we can try to set it if constraints allow, or just ensure is_superuser=True
        
        u.is_superuser = True
        u.is_staff = True
        u.save()
        
        # Set profile rank to ADMIN (max defined in choices)
        u.profile.rank = 'ADMIN'
        u.profile.save()
        
        print(f"Updated State - Superuser: {u.is_superuser}, Rank: {u.profile.rank}")
        
        # Verify RBAC value
        from src.Infrastructure.DjangoFramework.persistence.rbac import get_user_rank_value
        val = get_user_rank_value(u)
        print(f"RBAC Value: {val}")
        
        if val >= 100:
            print("SUCCESS: User has SUPERADMIN privileges.")
        else:
            print("WARNING: User value is below 100.")

    except User.DoesNotExist:
        print("User 'Alone' not found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    reset_alone_role()
