
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def verify_breadcrumbs():
    # 1. Create Scenario: Root (Data) -> Level2 (Empty) -> Level3 (Data)
    # IDs: 01 (Root), 0101 (L2), 010101 (L3)
    
    # Cleanup
    CaosWorldORM.objects.filter(id__startswith='99').delete()
    
    # Create Entities
    CaosWorldORM.objects.create(id='99', name="Root Test", description="Has Data", status="LIVE", is_active=True)
    CaosWorldORM.objects.create(id='9901', name="Empty Level", description=None, status="LIVE", is_active=True)
    CaosWorldORM.objects.create(id='990101', name="Deep Node", description="Has Data", status="LIVE", is_active=True)
    
    # 2. Generate Breadcrumbs for Deep Node
    crumbs = generate_breadcrumbs('990101')
    
    print("generated Breadcrumbs:")
    labels = []
    for c in crumbs:
        print(f" - {c['label']} (ID: {c['id']})")
        labels.append(c['label'])
        
    # 3. Verify
    if "Root Test" in labels:
        print("✅ PASS: Root is visible")
    else:
        print("❌ FAIL: Root is missing")
        
    if "Empty Level" not in labels:
        print("✅ PASS: Empty Level is HIDDEN")
    else:
        print("❌ FAIL: Empty Level is VISIBLE")
        
    if "Deep Node" in labels:
        print("✅ PASS: Deep Node (Current) is visible")
    else:
         print("❌ FAIL: Deep Node is missing")

    # Cleanup
    CaosWorldORM.objects.filter(id__startswith='99').delete()

if __name__ == '__main__':
    verify_breadcrumbs()
