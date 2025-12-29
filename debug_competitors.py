
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from django.db.models.functions import Length

print("--- LEVEL 2 ENTITIES (COMPETITORS) ---")
# Find all entities with ID length 2
competitors = CaosWorldORM.objects.annotate(id_len=Length('id')).filter(id_len=2)

for c in competitors:
    print(f"ID: {c.id} | Name: {c.name} | Status: {c.status}")

print("\n--- SPECIFIC CHECK FOR 01 ---")
try:
    w01 = CaosWorldORM.objects.get(id='01')
    print(f"01 EXISTS: {w01.name} (Status: {w01.status})")
except CaosWorldORM.DoesNotExist:
    print("01 DOES NOT EXIST")
