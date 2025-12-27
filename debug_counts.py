import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')

# MOCK: Remove 'theme' from INSTALLED_APPS if it causes issues for this script
# (Or just assume it works if run via manage.py shell)
# Better: Just run via manage.py shell logic
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def check_counts():
    try:
        try:
             alone = User.objects.get(username='Alone')
        except:
             print("User 'Alone' not found via get(). Checking all...")
             for u in User.objects.all(): print(f"- {u.username}")
             return

        print(f"User: {alone.username} (ID: {alone.id}, Superuser: {alone.is_superuser})")
        
        count_explicit = CaosWorldORM.objects.filter(author=alone).count()
        print(f"Worlds with author={alone.username}: {count_explicit}")
        
    except User.DoesNotExist:
        print("User 'Alone' not found.")

    count_orphans = CaosWorldORM.objects.filter(author__isnull=True).count()
    print(f"Worlds with author=None (Orphans): {count_orphans}")

    # Check Xico for comparison
    try:
        xico = User.objects.get(username='Xico')
        print(f"Worlds with author=Xico: {CaosWorldORM.objects.filter(author=xico).count()}")
    except: pass

if __name__ == "__main__":
    check_counts()
