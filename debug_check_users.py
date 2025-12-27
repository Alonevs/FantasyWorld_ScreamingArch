import os
import django
import sys

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.Infrastructure.DjangoFramework.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

try:
    alone = User.objects.get(username='Alone')
    print(f"User: {alone.username}, ID: {alone.id}")
    print(f"  Is Superuser: {alone.is_superuser}")
    print(f"  Is Staff: {alone.is_staff}")
except User.DoesNotExist:
    print("User 'Alone' not found!")

try:
    pepe = User.objects.get(username='Pepe')
    print(f"User: {pepe.username}")
    if hasattr(pepe, 'profile'):
        print(f"  Profile Rank: '{pepe.profile.rank}' (Type: {type(pepe.profile.rank)})")
        print(f"  Bosses: {[b.user.username for b in pepe.profile.bosses.all()]}")
    else:
        print("  No Profile!")
except User.DoesNotExist:
    print("User 'Pepe' not found!")
