
import os
import django
import sys

# Setup Django environment
sys.path.append('c:/Users/xico0/Desktop/FantasyWorld_ScreamingArch')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.main.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase
from django.contrib.auth.models import User

def verify():
    # 1. Get test world (Tierra Prime)
    world_id = "gLQ9buPL06"
    world = CaosWorldORM.objects.get(id=world_id)
    user = User.objects.first()
    
    print(f"--- Verificando Mundo: {world.name} ---")
    print(f"Metadata Actual: {world.metadata}")
    
    # 2. Propose Laws
    laws = {
        'planet_laws': {
            'global_temp': 'Helado',
            'sun_type': 'Sol Rojo',
            'base_element': 'Lava',
            'moons': ['Luna de Prueba'],
            'axial_tilt': 'Extrema'
        }
    }
    
    use_case_prop = ProposeChangeUseCase()
    ver_num = use_case_prop.execute(world_id, None, None, "Test Antigravity", user, metadata_proposal=laws)
    
    version = CaosVersionORM.objects.get(world=world, version_number=ver_num)
    print(f"Propuesta v{ver_num} creada con cambios: {version.cambios}")
    
    # 3. Approve Proposal
    # (Simulating approval status change)
    version.status = "APPROVED"
    version.save()
    
    use_case_pub = PublishToLiveVersionUseCase()
    use_case_pub.execute(version.id, reviewer=user)
    
    # 4. Verify Final State
    world.refresh_from_db()
    print(f"Metadata Final en JSONB: {world.metadata}")
    
    if 'planet_laws' in world.metadata and world.metadata['planet_laws']['global_temp'] == 'Helado':
        print("✅ ÉXITO: Los metadatos planetarios se han persistido correctamente.")
    else:
        print("❌ FALLO: Los metadatos no se encuentran en el objeto final.")

if __name__ == "__main__":
    verify()
