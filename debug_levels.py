import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def count_levels():
    all_active = CaosWorldORM.objects.filter(is_active=True).exclude(status='DELETED')
    counts = {}
    for m in all_active:
        level = len(m.id)
        counts[level] = counts.get(level, 0) + 1
    
    print("--- Entity Counts by ID Length ---")
    for level in sorted(counts.keys()):
        print(f"Length {level}: {counts[level]} entities")
    
    print("\nLength 2 entities:")
    for m in all_active:
        if len(m.id) == 2:
            print(f"[{m.id}] {m.name} ({m.public_id})")

if __name__ == '__main__':
    count_levels()
