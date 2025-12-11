
import os
import django
import sys

# Setup Path to Root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def clean_gaps():
    print("🧹 Cleaning Gaps...")
    
    # 1. Delete by Name
    deleted, _ = CaosWorldORM.objects.filter(name="_GAP_CONTAINER_").delete()
    print(f"   Deleted {deleted} entities named _GAP_CONTAINER_")
    
    # 2. Delete by Metadata Type using raw SQL or iterating if JSONField filtering issues arise normally
    # But current Django supports JSONField filtering if setup.
    # We used metadata={"type": "STRUCTURE_GAP"}
    
    # Try Filter
    # deleted_meta, _ = CaosWorldORM.objects.filter(metadata__type="STRUCTURE_GAP").delete()
    # print(f"   Deleted {deleted_meta} entities with type STRUCTURE_GAP")
    
    print("✅ Cleanup Complete.")

if __name__ == '__main__':
    clean_gaps()
