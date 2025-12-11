
import os
import django
import sys

# Setup Path to Root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase

def verify_direct_link():
    print("🚀 Verifying Direct Link with Padding...")
    repo = DjangoCaosRepository()
    
    # 1. Create Parent at Level 3 (Universo)
    p_id = "020202" # Different ID to avoid conflicts with previous tests
    CaosWorldORM.objects.filter(id__startswith=p_id).delete()
    CaosWorldORM.objects.create(id=p_id, name="Direct Link Test Universe", status="LIVE")
    print(f"✅ Created Parent: {p_id} (Level 3)")
    
    # 2. Execute Creation -> Level 8 (País) directly
    # Should produce ID with padding
    print("\n🐣 Executing Creation to Level 8 (Direct)...")
    uc = CreateChildWorldUseCase(repo)
    # Target Level 8. Parent Level 3. Gap 4 levels (4, 5, 6, 7).
    # ID structure: Parent(6) + Gap(8) + Child(2) = 16 chars.
    final_id = uc.execute(p_id, "Direct Country", "Testing padding", "Test", False, target_level=8)
    
    print(f"✅ Final Entity Created: {final_id}")
    
    # 3. Verify ID Structure
    # Should end with ...0000000001 (or similar seq)
    # Expected: 020202 + 00000000 + 01 (if first)
    expected_prefix = p_id + "00000000"
    if final_id.startswith(expected_prefix) and len(final_id) == 16:
        print("✅ ID Structure Correct: Padded correctly.")
    else:
        print(f"❌ ID Structure INCORRECT. Got {final_id}. Expected starts with {expected_prefix} and len 16.")

    # 4. Verify No Intermediate Gaps Exist
    intermediate_check = CaosWorldORM.objects.filter(id__startswith=p_id).exclude(id=p_id).exclude(id=final_id)
    if intermediate_check.count() == 0:
        print("✅ No intermediate entities found (Clean DB).")
    else:
        print(f"❌ Found unexpected intermediate entities: {[x.id for x in intermediate_check]}")
        
    # Set to LIVE
    w = CaosWorldORM.objects.get(id=final_id)
    w.status = 'LIVE'
    w.save()

    # 5. Verify Display (Orphan Finding Logic)
    print("\n👀 Verifying Display Logic (Orphan Finding)...")
    details_uc = GetWorldDetailsUseCase(repo)
    data = details_uc.execute(p_id)
    
    if not data:
        print("❌ Failed to fetch details")
        return

    hijos = data.get('hijos', [])
    print(f"Found {len(hijos)} visible children in Universe.")
    
    found = False
    for h in hijos:
        print(f" - {h['name']} ({h['id']}) [Hoisted/Deep: {h.get('is_hoisted')}]")
        if h['id'] == final_id:
            found = True
            
    if found:
        print("✅ SUCCESS: Direct Padded Child is visible!")
    else:
        print("❌ FAILURE: Direct Padded Child NOT visible.")
        
    # Cleanup
    # CaosWorldORM.objects.filter(id__startswith=p_id).delete()

if __name__ == '__main__':
    verify_direct_link()
