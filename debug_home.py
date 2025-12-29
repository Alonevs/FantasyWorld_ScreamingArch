import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.WorldManagement.Caos.Application.get_home_index import GetHomeIndexUseCase
from django.db.models import Q

def debug():
    ms = CaosWorldORM.objects.filter(is_active=True).exclude(status='DELETED')
    
    print("--- RAW CANDIDATES (0101, 0102) ---")
    for m in CaosWorldORM.objects.filter(id__in=['0101', '0102']):
        print(f"ID={m.id}, Status={m.status}, Public={m.visible_publico}, DescLen={len(m.description or '')}")

    # The filter that might exclude 0101
    ms_excluded = ms.filter(
        Q(description__isnull=True) | Q(description__exact='') | Q(description__iexact='None'),
        ~Q(public_id='JhZCO1vxI7')
    )
    print("\n--- WOULD BE EXCLUDED BY DESC CHECK ---")
    for m in ms_excluded.filter(id__in=['0101', '0102']):
        print(f"EXCLUDED: {m.id} ({m.name})")

if __name__ == '__main__':
    debug()
