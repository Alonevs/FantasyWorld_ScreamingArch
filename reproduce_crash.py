
import os
import sys
import django
from django.conf import settings

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), 'src', 'Infrastructure', 'DjangoFramework'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
from src.Infrastructure.DjangoFramework.persistence.utils import get_world_images
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

target_id = "JhZCO1vxI7"

print(f"--- TESTING ID: {target_id} ---")

try:
    print("1. Calling get_world_images directly...")
    imgs = get_world_images(target_id)
    print(f"   Images found: {len(imgs)}")
except Exception as e:
    print(f"!!! CRASH in get_world_images: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Calling GetWorldDetailsUseCase...")
try:
    repo = DjangoCaosRepository()
    context = GetWorldDetailsUseCase(repo).execute(target_id, None)
    print("   Context retrieved successfully.")
    if context:
        print(f"   Name: {context.get('name')}")
        print(f"   Children: {len(context.get('hijos', []))}")
except Exception as e:
    print(f"!!! CRASH in UseCase: {e}")
    import traceback
    traceback.print_exc()
