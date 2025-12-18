
import os
import sys
import django

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def fix():
    print("--- FIXING HIERARCHY ---")
    
    # Check if 0100 exists
    if CaosWorldORM.objects.filter(id='0100').exists():
        print("✅ World 0100 already exists.")
        return

    # Get Root 01 to inherit author/permissions
    try:
        root = CaosWorldORM.objects.get(id='01')
    except CaosWorldORM.DoesNotExist:
        print("❌ CRITICAL: Root world '01' not found. Cannot infer context.")
        return

    print(f"Creating '0100' (Child of {root.name})...")
    
    w = CaosWorldORM.objects.create(
        id='0100',
        name="Nexo Nivel 2 (Restaurado)",
        description="Entidad estructural generada automáticamente para restaurar la jerarquía.",
        status='LIVE',
        visible_publico=True,
        author=root.author,
        current_version_number=1,
        allow_proposals=True
    )
    
    print(f"✨ Created: [{w.id}] {w.name}")
    print("Hierarchy should now be repaired.")

if __name__ == "__main__":
    fix()
