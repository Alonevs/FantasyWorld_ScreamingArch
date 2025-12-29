import os
import sys
import django
from django.utils.text import slugify

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, 
    TimelinePeriod, 
    TimelinePeriodVersion
)
from django.contrib.auth.models import User

def migrate():
    print("--- Iniciando migración de timelines históricos ---")
    
    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    worlds = CaosWorldORM.objects.filter(is_active=True)
    
    total_periods = 0
    
    for world in worlds:
        timeline = world.metadata.get('timeline')
        if not timeline:
            continue
            
        print(f"\n[ENTIDAD] Procesando: {world.name} ({world.public_id})")
        
        for year, snapshot in timeline.items():
            title = f"Año {year}"
            slug = slugify(title)
            
            # Evitar duplicados
            if TimelinePeriod.objects.filter(world=world, slug=slug).exists():
                print(f"  [SKIPPED] Periodo '{title}' ya existe.")
                continue
                
            description = snapshot.get('description', '')
            metadata = snapshot.get('metadata', {})
            
            try:
                # Crear Periodo
                period = TimelinePeriod.objects.create(
                    world=world,
                    title=title,
                    slug=slug,
                    description=description,
                    order=int(year) if year.isdigit() else 0,
                    is_current=False
                )
                
                # Crear Version Aprobada (V1)
                TimelinePeriodVersion.objects.create(
                    period=period,
                    version_number=1,
                    proposed_title=title,
                    proposed_description=description,
                    status='APPROVED',
                    author=admin_user,
                    change_log='Migracion automatica desde metadata JSON'
                )
                
                total_periods += 1
                print(f"  [OK] Migrado: {title}")
                
            except Exception as e:
                import traceback
                print(f"  [ERROR] Al migrar {title}: {e}")
                traceback.print_exc()

    print(f"\n--- Migración finalizada. Se crearon {total_periods} periodos históricos ---")

if __name__ == "__main__":
    migrate()
