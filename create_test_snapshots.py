"""
Script para crear un snapshot de Timeline de prueba y poder ver el selector.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from django.contrib.auth.models import User

print("🧪 Creando Snapshot de Timeline de Prueba\n")
print("=" * 60)

# Obtener primera entidad activa
world = CaosWorldORM.objects.filter(is_active=True).first()
if not world:
    print("❌ No hay entidades en la BD")
    sys.exit(1)

print(f"✅ Entidad: {world.name} ({world.public_id or world.id})")

# Verificar si ya tiene timeline
if world.metadata and 'timeline' in world.metadata:
    print(f"📅 Ya tiene {len(world.metadata['timeline'])} snapshots:")
    for year in sorted(world.metadata['timeline'].keys()):
        print(f"   - Año {year}")
else:
    print("📅 No tiene snapshots aún")

# Crear snapshots de prueba directamente en metadata
print("\n🔧 Creando snapshots de prueba...")

if not world.metadata:
    world.metadata = {}

if 'timeline' not in world.metadata:
    world.metadata['timeline'] = {}

# Snapshot 1: Año 1500
world.metadata['timeline']['1500'] = {
    'description': f'En el año 1500, {world.name} era una tierra próspera y floreciente. Las ciudades bullían de actividad comercial y los campos estaban llenos de cultivos abundantes.',
    'metadata': {
        'datos_nucleo': {
            'poblacion': '50000',
            'gobierno': 'Monarquía',
            'estado': 'Próspera'
        }
    },
    'images': [],
    'cover_image': None
}

# Snapshot 2: Año 1750
world.metadata['timeline']['1750'] = {
    'description': f'Para el año 1750, {world.name} había experimentado grandes cambios. La revolución industrial comenzaba a transformar el paisaje, con fábricas emergiendo en las ciudades principales.',
    'metadata': {
        'datos_nucleo': {
            'poblacion': '120000',
            'gobierno': 'República',
            'estado': 'En Expansión'
        }
    },
    'images': [],
    'cover_image': None
}

# Snapshot 3: Año 2000
world.metadata['timeline']['2000'] = {
    'description': f'En el año 2000, {world.name} se había convertido en una metrópolis moderna. Rascacielos dominaban el horizonte y la tecnología estaba presente en cada aspecto de la vida cotidiana.',
    'metadata': {
        'datos_nucleo': {
            'poblacion': '500000',
            'gobierno': 'Democracia',
            'estado': 'Avanzada'
        }
    },
    'images': [],
    'cover_image': None
}

# Guardar
world.save()

print("\n✅ Snapshots creados exitosamente!")
print(f"\n📊 Timeline de {world.name}:")
for year in sorted(world.metadata['timeline'].keys()):
    snapshot = world.metadata['timeline'][year]
    desc_preview = snapshot['description'][:60] + '...'
    print(f"\n   📜 Año {year}:")
    print(f"      {desc_preview}")
    if 'metadata' in snapshot and 'datos_nucleo' in snapshot['metadata']:
        nucleo = snapshot['metadata']['datos_nucleo']
        print(f"      Población: {nucleo.get('poblacion', 'N/A')}")
        print(f"      Gobierno: {nucleo.get('gobierno', 'N/A')}")

print("\n" + "=" * 60)
print("✅ ¡Listo! Ahora ve a la entidad para ver el selector temporal:")
print(f"   http://127.0.0.1:8000/mundo/{world.public_id or world.id}/")
print("\n💡 Deberías ver:")
print("   - Selector con 4 opciones: ACTUAL, 1500, 1750, 2000")
print("   - Click en cualquier año para ver ese snapshot")
print("   - La descripción cambiará según el año seleccionado")
