import os
import sys
from pathlib import Path
import django
import json

# Setup path to project root
current_path = Path(__file__).resolve().parent
project_root = current_path.parents[1]
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'src' / 'Infrastructure' / 'DjangoFramework'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import MetadataTemplate
# Importar el script hermano
from src.scripts.init_constants import seed_constants

def seed_chaos_template():
    # 1. ACTUALIZAR PLANTILLA (MODO DINÁMICO)
    schema = {
        "dynamic_mode": True,
        "ui_config": {"icon": "fa-atom", "color": "purple"}
    }
    
    ui_config = {
        "theme": "chaos_dark",
        "icon": "metapod_chaos_icon",
        "background_style": "void_noise"
    }

    # Actualizamos CHAOS, PLANET, CREATURE para que todos sean dinámicos
    for etype in ['CHAOS', 'PLANET', 'CREATURE']:
        obj, created = MetadataTemplate.objects.update_or_create(
            entity_type=etype,
            defaults={
                'schema_definition': schema,
                'ui_config': ui_config
            }
        )
        print(f"Plantilla '{etype}' actualizada a Modo Dinámico.")

    # 2. LIMPIEZA DE METADATOS VIEJOS (ROOT)
    # Buscamos por ID '01' que suele ser el Root en este sistema
    from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
    try:
        w = CaosWorldORM.objects.get(id_codificado='01')
        w.metadata = {}  # Wipe clean
        w.save()
        print(f"🧹 METADATA RESET: 'Caos Prime' (01) ha sido limpiado.")
    except CaosWorldORM.DoesNotExist:
        try:
            # Fallback a J-ID
            w = CaosWorldORM.objects.get(id='01') 
            w.metadata = {}
            w.save()
            print(f"🧹 METADATA RESET: 'Caos Prime' (id=01) ha sido limpiado.")
        except:
             print("⚠️ No se encontró 'Caos Prime' para resetear metadatos.")

if __name__ == '__main__':
    seed_chaos_template()
