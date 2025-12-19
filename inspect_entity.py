
import os
import sys
import django

# Setup Django Environment
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src')) 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def inspect_entity():
    pid = "SMDmFoz8I9"
    print(f"🚀 INSPECTING: {pid}")
    
    with open('inspect_result.txt', 'w', encoding='utf-8') as f:
        try:
            w = CaosWorldORM.objects.get(public_id=pid)
            f.write(f"✅ ID: {w.id} | Name: {w.name} | Status: {w.status}\n")
            
            # Check descendants
            descendants = CaosWorldORM.objects.filter(id__startswith=w.id).exclude(id=w.id).order_by('id')
            f.write(f"📋 Descendants ({descendants.count()}):\n")
            for d in descendants:
                f.write(f"   - [{d.id}] {d.name} (Status: {d.status})\n")
                
        except CaosWorldORM.DoesNotExist:
            f.write(f"❌ Entity {pid} not found.\n")
    print("Done.")

inspect_entity()
