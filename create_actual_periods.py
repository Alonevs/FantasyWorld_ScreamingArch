"""
Script para crear período ACTUAL para todas las entidades existentes.
Ejecutar una sola vez después de aplicar la migración.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, TimelinePeriod, TimelinePeriodVersion
from django.contrib.auth.models import User
from django.utils.text import slugify

print("🔧 Creando períodos ACTUAL para entidades existentes\n")
print("=" * 60)

# Obtener todas las entidades activas
worlds = CaosWorldORM.objects.filter(is_active=True)
total = worlds.count()

print(f"📊 Entidades encontradas: {total}\n")

created_count = 0
skipped_count = 0

# Obtener usuario admin para versión inicial
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.first()

for i, world in enumerate(worlds, 1):
    # Verificar si ya tiene período ACTUAL
    existing = TimelinePeriod.objects.filter(world=world, is_current=True).exists()
    
    if existing:
        print(f"[{i}/{total}] ⏭️  {world.name} - Ya tiene período ACTUAL")
        skipped_count += 1
        continue
    
    try:
        # Crear período ACTUAL
        period = TimelinePeriod.objects.create(
            world=world,
            title='ACTUAL',
            slug='actual',
            description=world.description or '',
            order=999,  # Siempre al final
            is_current=True
        )
        
        # Crear versión inicial (V1)
        TimelinePeriodVersion.objects.create(
            period=period,
            version_number=1,
            proposed_title='ACTUAL',
            proposed_description=world.description or '',
            status='APPROVED',
            author=admin_user,
            change_log='Creación automática del período ACTUAL'
        )
        
        print(f"[{i}/{total}] ✅ {world.name} - Período ACTUAL creado")
        created_count += 1
        
    except Exception as e:
        print(f"[{i}/{total}] ❌ {world.name} - Error: {e}")

print("\n" + "=" * 60)
print(f"✅ Períodos creados: {created_count}")
print(f"⏭️  Omitidos (ya existían): {skipped_count}")
print(f"📊 Total procesado: {total}")
print("\n💡 Ahora todas las entidades tienen su período ACTUAL")
