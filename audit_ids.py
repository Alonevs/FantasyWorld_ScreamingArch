
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
import re

def audit_ids():
    # Fetch all worlds potentially visible
    qs = CaosWorldORM.objects.all().order_by('id')
    
    with open('audit_results.txt', 'w', encoding='utf-8') as f:
        f.write(f"--- WORLD AUDIT ({qs.count()}) ---\n")
        needs_migration = []
        
        for w in qs:
            pid = w.public_id
            is_nano = False
            # Simple check: 10 chars and valid nanoid chars
            if pid and len(pid) == 10 and re.match(r'^[A-Za-z0-9_-]+$', pid):
                is_nano = True
                
            status = "OK" if is_nano else "LEGACY/SLUG"
            f.write(f"[{w.id}] {w.name} | PID: {pid} | {status}\n")
            
            if not is_nano:
                needs_migration.append(w.id)
                
        f.write(f"--- NEEDS MIGRATION: {len(needs_migration)} ---\n")
        f.write(str(needs_migration))

if __name__ == "__main__":
    audit_ids()
