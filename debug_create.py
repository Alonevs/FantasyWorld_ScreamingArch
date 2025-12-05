import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_narrative import CreateNarrativeUseCase
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

try:
    print("Testing Creation...")
    repo = DjangoCaosRepository()
    # Pick first world
    w = CaosWorldORM.objects.first()
    if not w:
        print("No world found.")
        exit()
        
    print(f"Creating in World: {w.name} ({w.id})")
    
    uc = CreateNarrativeUseCase(repo)
    nid = uc.execute(
        world_id=w.id,
        tipo_codigo='L',
        title="Debug Creation",
        content="Debug Content",
        publish_immediately=False
    )
    print(f"SUCCESS. Created NID: {nid}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
