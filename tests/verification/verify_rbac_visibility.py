import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
sys.path.append(os.path.join(os.getcwd(), 'src', 'Infrastructure', 'DjangoFramework'))
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import UserProfile

def verify_visibility_logic(username):
    try:
        user = User.objects.get(username=username)
        print(f"\n--- Checking visibility for: {user.username} (Rank: {user.profile.rank}) ---")
        
        visible_ids = [user.id]
        if hasattr(user, 'profile'):
            collab_ids = list(user.profile.collaborators.values_list('user__id', flat=True))
            boss_ids = list(user.profile.bosses.values_list('user__id', flat=True))
            print(f"Subordinates IDs: {collab_ids}")
            print(f"Bosses IDs: {boss_ids}")
            visible_ids.extend(collab_ids)
            visible_ids.extend(boss_ids)
        
        visible_names = list(User.objects.filter(id__in=visible_ids).values_list('username', flat=True))
        print(f"Users whose work is visible to {username}: {visible_names}")
        
    except User.DoesNotExist:
        print(f"User {username} not found.")

if __name__ == "__main__":
    # Test with known users if possible, or just print logic proof
    users = User.objects.all()[:5]
    for u in users:
        verify_visibility_logic(u.username)
