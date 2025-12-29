
import os
import sys
import django

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

target_pid = 'JhZCO1vxI7'
print(f"--- DEBUGGING WORLD {target_pid} ---")

try:
    w = CaosWorldORM.objects.get(public_id=target_pid)
    print(f"FOUND: {w}")
    print(f"  ID (Internal): {w.id}")
    print(f"  Public ID: {w.public_id}")
    print(f"  Name: {w.name}")
    print(f"  Status: {w.status}")
    print(f"  Visible Publico: {w.visible_publico}")
    print(f"  Is Active: {w.is_active}")
    print(f"  Owner: {w.author} (ID: {w.author_id})")
    
    trunk_id = w.id
    if '00' in w.id:
         if len(w.id) // 2 < 7:
             trunk_id = w.id.split('00')[0]
             print(f"  [Logic Check] Detected '00'. Trunk calculated as: {trunk_id}")
    
    similar = CaosWorldORM.objects.filter(id__startswith=trunk_id)
    print(f"  [Collision Check] Entities starting with trunk '{trunk_id}':")
    for s in similar:
        print(f"    - {s.id} | {s.public_id} | {s.name} | Status: {s.status}")

except CaosWorldORM.DoesNotExist:
    print("❌ ERROR: World not found in DB with that public_id")
except Exception as e:
    print(f"❌ ERROR: {e}")
