
import os
import django
import sys

# Setup Path to Root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.settings')
django.setup()

from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.deep_creation_service import DeepCreationService
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase

def verify_deep_creation():
    print("🚀 Verifying Deep Creation Service...")
    repo = DjangoCaosRepository()
    
    # 1. Create Parent at Level 3 (Universo)
    # Level 3 = 6 chars (010101)
    p_id = "010101"
    CaosWorldORM.objects.filter(id__startswith=p_id).delete()
    CaosWorldORM.objects.create(id=p_id, name="Test Universe", status="LIVE")
    print(f"✅ Created Parent: {p_id} (Level 3)")
    
    # 2. Execute Deep Creation -> Level 8 (País)
    # Gaps needed: 4, 5, 6, 7
    print("\n🐣 Executing Deep Creation to Level 8...")
    svc = DeepCreationService(repo)
    final_id = svc.create_descendant_at_level(p_id, 8, "Deep Test Country", "Testing deep dive", "Test")
    
    print(f"✅ Final Entity Created: {final_id}")
    
    # 3. Verify Gaps
    # Level 4 Gap: 01010100
    gap4 = CaosWorldORM.objects.filter(id="01010100").first()
    print(f"   Gap L4 exists: {gap4 is not None}")
    
    # Level 5 Gap: 0101010000
    gap5 = CaosWorldORM.objects.filter(id="0101010000").first()
    print(f"   Gap L5 exists: {gap5 is not None}")

    # Level 6 Gap: 010101000000
    gap6 = CaosWorldORM.objects.filter(id="010101000000").first()
    print(f"   Gap L6 exists: {gap6 is not None}")

    # Level 7 Gap: 01010100000000
    gap7 = CaosWorldORM.objects.filter(id="01010100000000").first()
    print(f"   Gap L7 exists: {gap7 is not None}")
    
    # Level 8 should be under Gap 7
    if final_id.startswith("01010100000000") and len(final_id) == 16:
        print("✅ Final Entity has correct ID structure for Level 8 under gaps.")
    else:
        print(f"❌ Final Entity ID {final_id} is strange.")

    # 4. Set Final Entity to LIVE (Standard creation makes it DRAFT via repo usually? 
    # CreateChildUseCase sets DRAFT by default. DeepCreationService uses it.)
    
    # Set to LIVE to verify display
    w_final = CaosWorldORM.objects.get(id=final_id)
    w_final.status = 'LIVE'
    w_final.save()
    print("   Set Final Entity to LIVE for display test.")

    # 5. Verify Recursive Hoisting
    print("\n👀 Verifying Recursive Hoisting (Universo -> Country)...")
    details_uc = GetWorldDetailsUseCase(repo)
    data = details_uc.execute(p_id)
    
    if not data:
        print("❌ Failed to fetch details")
        return

    hijos = data.get('hijos', [])
    print(f"Found {len(hijos)} visible children in Universe.")
    
    found = False
    for h in hijos:
        print(f" - {h['name']} ({h['id']}) [Hoisted: {h.get('is_hoisted')}]")
        if h['id'] == final_id:
            found = True
            
    if found:
        print("✅ SUCCESS: Deep Country is visible from Universe (Level 3)!")
    else:
        print("❌ FAILURE: Deep Country NOT visible.")

    # Cleanup (Optional)
    # CaosWorldORM.objects.filter(id__startswith=p_id).delete()

if __name__ == '__main__':
    verify_deep_creation()
