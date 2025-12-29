import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

print("\n--- CHECKING CAOS PRIME ---")
worlds = CaosWorldORM.objects.filter(name__icontains='Caos Prime')
if not worlds:
    print("No world found with name containing 'Caos Prime'")
else:
    for w in worlds:
        print(f"ID: {w.id} | Name: {w.name} | Status: {w.status} | Active: {w.is_active} | PublicID: {w.public_id}")

print("\n--- CHECKING ALL WORLDS (ID, Name) ---")
all_worlds = CaosWorldORM.objects.all().order_by('id')
for w in all_worlds:
    print(f"ID: {w.id} | Name: {w.name}")
