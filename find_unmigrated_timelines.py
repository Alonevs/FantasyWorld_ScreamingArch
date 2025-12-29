import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, TimelinePeriod

print("🔍 Buscando entidades con timeline en JSON...")
worlds = CaosWorldORM.objects.filter(is_active=True)
found = 0

for w in worlds:
    timeline = w.metadata.get('timeline')
    if timeline:
        found += 1
        print(f"\nEntidad: {w.name} ({w.public_id})")
        print(f"  Años encontrados en JSON: {list(timeline.keys())}")
        
        # Verificar si ya tienen periodos correspondientes
        for year in timeline.keys():
            exists = TimelinePeriod.objects.filter(world=w, slug__contains=str(year)).exists()
            status = "✅ Migrado (o existe slug similar)" if exists else "❌ NO MIGRADO"
            print(f"    - Año {year}: {status}")

if found == 0:
    print("No se encontraron entidades con el campo 'timeline' en su metadata JSON.")
else:
    print(f"\nTotal entidades con JSON timeline: {found}")
