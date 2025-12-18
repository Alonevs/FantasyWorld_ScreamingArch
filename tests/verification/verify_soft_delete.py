
import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def verify_soft_delete():
    # 1. Create Test Entity
    test_id = "test_sd_01"
    CaosWorldORM.objects.filter(id=test_id).delete() # Cleanup
    w = CaosWorldORM.objects.create(id=test_id, name="Test Soft Delete", status='DRAFT')
    print(f"[SETUP] Created {w.name} Active={w.is_active}")

    # 2. Soft Delete
    w.soft_delete()
    w.refresh_from_db()
    print(f"[ACTION] Soft Deleted. Active={w.is_active}, DeletedAt={w.deleted_at}")

    if w.is_active:
        print("❌ FAIL: Entity should be inactive")
        return

    # 3. Verify Repository/ORM visibility
    try:
        CaosWorldORM.objects.get(id=test_id, is_active=True)
        print("❌ FAIL: Should not be able to get active entity")
    except CaosWorldORM.DoesNotExist:
        print("✅ PASS: Entity is hidden from active queries")

    # 4. Verify Trash Visibility
    trash_item = CaosWorldORM.objects.filter(id=test_id, is_active=False).first()
    if trash_item:
        print("✅ PASS: Entity visible in trash")
    else:
        print("❌ FAIL: Entity missing from trash")

    # 5. Restore
    w.restore()
    w.refresh_from_db()
    print(f"[ACTION] Restored. Active={w.is_active}")

    try:
        CaosWorldORM.objects.get(id=test_id, is_active=True)
        print("✅ PASS: Entity restored and visible")
    except:
        print("❌ FAIL: Entity not restored correctly")

    # Cleanup
    w.delete()
    print("[CLEANUP] Done")

if __name__ == '__main__':
    verify_soft_delete()
