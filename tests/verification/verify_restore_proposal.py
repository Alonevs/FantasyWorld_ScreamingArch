
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase

def verify_restore_proposal():
    # 1. Setup
    test_id = "test_restore_prop"
    CaosWorldORM.objects.filter(id=test_id).delete()
    w = CaosWorldORM.objects.create(id=test_id, name="Test Restore Proposal", status='DRAFT')
    
    # 2. Soft Delete
    print(f"[SETUP] Soft Deleting {w.name}...")
    w.soft_delete()
    w.refresh_from_db()
    
    if w.is_active:
        print("❌ FAIL: Entity should be inactive")
        return

    # 3. Simulate "Restore Request" (Create Proposal)
    # Logic copied from view
    print("[ACTION] Creating Restore Proposal...")
    v = CaosVersionORM.objects.create(
        world=w,
        proposed_name=w.name,
        proposed_description=w.description,
        version_number=2,
        status='PENDING',
        cambios={'action': 'RESTORE'}
    )
    
    # 4. Check State: Should still be inactive
    w.refresh_from_db()
    if w.is_active:
        print("❌ FAIL: Entity became active BEFORE proposal approval")
    else:
        print("✅ PASS: Entity remains inactive pending approval")

    # 5. Approve & Publish
    print("[ACTION] Approving & Publishing Proposal...")
    v.status = 'APPROVED'
    v.save()
    
    # Execute Publish Logic
    PublishToLiveVersionUseCase().execute(v.id)
    
    # 6. Verify Restoration
    w.refresh_from_db()
    v.refresh_from_db()

    if w.is_active and v.status == 'LIVE':
        print(f"✅ PASS: Entity RESTORED successfully. Active={w.is_active}")
    else:
        print(f"❌ FAIL: Restoration failed. Active={w.is_active}, VersionStatus={v.status}")

    # Cleanup
    w.delete()
    print("[CLEANUP] Done")

if __name__ == '__main__':
    verify_restore_proposal()
