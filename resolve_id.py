
import os
import django
import sys

# Setup Django environment
sys.path.append(r'c:\Users\xico0\Desktop\FantasyWorld_ScreamingArch')
sys.path.append(r'c:\Users\xico0\Desktop\FantasyWorld_ScreamingArch\src\Infrastructure\DjangoFramework')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

try:
    target_pid = "glAEReZ7b6"
    world = CaosWorldORM.objects.filter(public_id=target_pid).first()
    if world:
        parent_id = world.id[:-2]
        parent = CaosWorldORM.objects.filter(id=parent_id).first()
        parent_name = parent.name if parent else "UNKNOWN/ROOT"
        
        print(f"\n--- ENTITY ---", flush=True)
        print(f"ID: {world.id}", flush=True)
        print(f"Name: {world.name}", flush=True)
        print(f"Status: {world.status}", flush=True)
        print(f"Parent: {parent_name} ({parent_id})", flush=True)
        print(f"---------------", flush=True)

        # Deletion logic if argument provided
        if len(sys.argv) > 1 and sys.argv[1] == '--delete':
            world.status = 'DELETED'
            world.save()
            print(f"✅ ACTION: Entity '{world.name}' set to DELETED.", flush=True)
    else:
        print(f"NOT FOUND: {target_pid}", flush=True)
        
except Exception as e:
    print(f"Error: {e}")
