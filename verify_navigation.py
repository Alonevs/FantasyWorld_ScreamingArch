import os
import django
import sys

# Setup Django environment
sys.path.append('d:\\FantasyWorld_ScreamingArch')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.views import generate_breadcrumbs
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def test_generate_breadcrumbs():
    print("Testing generate_breadcrumbs...")
    
    # Create dummy worlds for testing
    # Level 1: 10
    # Level 2: 1020
    # Level 3: 102030
    # ...
    # Level 15: ...
    # Level 16 (Entity): ... + 1234
    
    # We need to ensure these worlds exist or at least the function handles missing ones gracefully (it uses .get with default)
    # But to test labels, we should create them.
    
    w1 = CaosWorldORM.objects.create(id="99", name="Level 1 World", description="Test")
    w2 = CaosWorldORM.objects.create(id="9988", name="Level 2 World", description="Test")
    w3 = CaosWorldORM.objects.create(id="998877", name="Level 3 World", description="Test")
    
    # Test Level 1
    b1 = generate_breadcrumbs("99")
    print(f"Breadcrumbs for 99: {b1}")
    assert len(b1) == 1
    assert b1[0]['id'] == "99"
    assert b1[0]['label'] == "Level 1 World"
    
    # Test Level 2
    b2 = generate_breadcrumbs("9988")
    print(f"Breadcrumbs for 9988: {b2}")
    assert len(b2) == 2
    assert b2[0]['id'] == "99"
    assert b2[1]['id'] == "9988"
    assert b2[1]['label'] == "Level 2 World"
    
    # Test Level 3
    b3 = generate_breadcrumbs("998877")
    print(f"Breadcrumbs for 998877: {b3}")
    assert len(b3) == 3
    assert b3[2]['id'] == "998877"
    
    # Test Entity Level (Level 16)
    # ID length: 15*2 = 30 chars + 4 chars = 34 chars
    # Let's simulate a deep ID
    deep_id_parent = "99" + "00"*14 # 30 chars
    entity_id = deep_id_parent + "1234" # 34 chars
    
    # We won't create the DB objects for this deep one, just check ID parsing
    b_deep = generate_breadcrumbs(entity_id)
    print(f"Breadcrumbs for deep ID (len {len(entity_id)}): {len(b_deep)} crumbs")
    
    # Should have 16 crumbs
    assert len(b_deep) == 16
    # Last one should be the entity
    assert b_deep[-1]['id'] == entity_id
    # Penultimate should be the parent
    assert b_deep[-2]['id'] == deep_id_parent
    
    # Cleanup
    w1.delete()
    w2.delete()
    w3.delete()
    
    print("✅ generate_breadcrumbs passed!")

if __name__ == "__main__":
    try:
        test_generate_breadcrumbs()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
