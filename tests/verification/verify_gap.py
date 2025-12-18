
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
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase

def verify_gap_logic():
    print("🚀 Verifying Level 12 Gap Logic...")
    repo = DjangoCaosRepository()
    
    # 1. Create Level 11 Parent (Mock)
    # Level 11 is 22 chars. Let's create a fake one if not exists.
    # Level 9 (City) -> 18 Chars
    # Level 10 (District) -> 20 Chars
    # Level 11 (Place) -> 22 Chars
    # Let's clean up test data first to be sure
    test_p_id = "0101010101010101010101" # 22 chars. 
    CaosWorldORM.objects.filter(id=test_p_id).delete()
    CaosWorldORM.objects.filter(id__startswith=test_p_id).delete()
    
    # Store Parent in DB
    p_orm = CaosWorldORM.objects.create(id=test_p_id, name="Test Level 11", status="LIVE")
    print(f"✅ Created Test Parent: {test_p_id}")
    
    # 2. Execute Create Child
    print("\n🐣 Creating Child under Level 11...")
    uc = CreateChildWorldUseCase(repo)
    new_id = uc.execute(test_p_id, "Test Child 13", "Should be under Gap")
    
    # 3. Verify Gap Creation
    gap_id = test_p_id + "00"
    try:
        gap = CaosWorldORM.objects.get(id=gap_id)
        print(f"✅ Gap Created: {gap.id} - {gap.name}")
    except:
        print(f"❌ GAP NOT CREATED at {gap_id}")
        return

    # Set Child to LIVE to verify hoisting (since drafts are hidden)
    child = CaosWorldORM.objects.get(id=new_id)
    child.status = 'LIVE'
    child.save()

    # 4. Verify Child ID
    print(f"✅ Child ID: {new_id}")
    if new_id.startswith(gap_id):
        print("✅ Child is correctly under Gap")
    else:
        print(f"❌ Child ID {new_id} is NOT under Gap {gap_id}")

    # 5. Verify Hoisting
    print("\n👀 Verifying Display Hoisting...")
    # Need to verify GetWorldDetailsUseCase returns the child in the list of parent
    details_uc = GetWorldDetailsUseCase(repo)
    data = details_uc.execute(test_p_id)
    
    if not data:
        print("❌ Failed to get details")
    else:
        hijos = data.get('hijos', [])
        print(f"Found {len(hijos)} children displayed.")
        found = False
        for h in hijos:
            print(f" - {h['name']} ({h['id']}) [Hoisted: {h.get('is_hoisted')}]")
            if h['id'] == new_id:
                found = True
        
        if found:
            print("✅ Child 13 is VISIBLE in Level 11 View (Hoisted)")
        else:
            print("❌ Child 13 is NOT visible in Level 11 View")

    # Cleanup
    # CaosWorldORM.objects.filter(id__startswith=test_p_id).delete()
    # CaosWorldORM.objects.filter(id=test_p_id).delete()
    print("\n🏁 Verification Complete.")

if __name__ == '__main__':
    verify_gap_logic()
