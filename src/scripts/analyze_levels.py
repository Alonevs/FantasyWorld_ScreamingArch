
import os
import django
from django.db.models.functions import Length

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def analyze_levels():
    all_worlds = CaosWorldORM.objects.filter(is_active=True).order_by('id')
    print("--- ALL WORLDS ---")
    for w in all_worlds:
        print(f"ID: {w.id} (Len: {len(w.id)}) - {w.name}")

    print("\n--- FILTERED (Len <= 4) ---")
    filtered = CaosWorldORM.objects.annotate(id_len=Length('id')).filter(id_len__lte=4, is_active=True).order_by('id')
    for w in filtered:
        print(f"ID: {w.id} - {w.name}")

if __name__ == '__main__':
    analyze_levels()
