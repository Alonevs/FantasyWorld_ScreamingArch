
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
import json

def list_gallery():
    worlds = CaosWorldORM.objects.filter(is_active=True)
    for world in worlds:
        if world.metadata and 'gallery_log' in world.metadata:
            log = world.metadata['gallery_log']
            print(f"World: {world.name} ({world.public_id})")
            for filename in log.keys():
                print(f"  - |{filename}|")

if __name__ == "__main__":
    list_gallery()
