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

from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosNarrativeVersionORM, MetadataTemplate, CaosWorldORM
from src.scripts.init_constants import seed_constants

def clean_and_reset():
    print("🧹 INICIANDO LIMPIEZA DEL SISTEMA...")

    # 1. BORRAR VERSIONES BASURA
    # Borramos propuestas pendientes o rechazadas para limpiar el dashboard
    deleted_v, _ = CaosVersionORM.objects.filter(status__in=['PENDING', 'REJECTED']).delete()
    deleted_nv, _ = CaosNarrativeVersionORM.objects.filter(status__in=['PENDING', 'REJECTED']).delete()
    
    print(f" ✅ Eliminadas {deleted_v} versiones de mundo basura.")
    print(f" ✅ Eliminadas {deleted_nv} versiones narrativas basura.")

    # 2. ACTUALIZAR PLANTILLA CHAOS (MODO DINÁMICO PURO)
    constantes_data = seed_constants()
    
    # Esquema limpio: Solo UI config + Flag Dinámico + Constantes (único campo fijo útil)
    new_schema = {
        "dynamic_mode": True,
        "ui_config": {
            "icon": "fa-atom", 
            "color": "purple"
        },
        # Mantenemos constantes porque es útil para selects, aunque el modal sea dinámico
        "constantes": {
            "type": "entity_list", 
            "label": "Constantes Cosmológicas", 
            "values": constantes_data
        }
    }
    
    ui_config = {
        "theme": "chaos_dark", 
        "icon": "metapod_chaos_icon"
    }

    # Aplicar a CHAOS (y por seguridad a PLANET y CREATURE para uniformidad)
    for etype in ['CHAOS', 'PLANET', 'CREATURE']:
        MetadataTemplate.objects.update_or_create(
            entity_type=etype,
            defaults={
                'schema_definition': new_schema,
                'ui_config': ui_config
            }
        )
    print(" ✅ Plantillas (CHAOS/PLANET/CREATURE) reseteadas a Modo Dinámico.")
    
    # 3. LIMPIEZA DE DATOS EN CAOS PRIME (ID 01)
    # Para asegurar que la extracción de prueba sea limpia
    try:
        w = CaosWorldORM.objects.filter(id_codificado='01').first()
        if not w: w = CaosWorldORM.objects.filter(id='01').first()
        
        if w:
            w.metadata = {} 
            w.save()
            print(f" ✅ Metadata de '{w.name}' limpiada.")
    except Exception as e:
        print(f" ⚠️ No se pudo limpiar metadata de Root: {e}")

if __name__ == '__main__':
    clean_and_reset()
