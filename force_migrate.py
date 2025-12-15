
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
import re
import nanoid

def generate_nanoid():
    return nanoid.generate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-', 10)

def force_migrate():
    qs = CaosWorldORM.objects.exclude(status='DRAFT').exclude(description__isnull=True).exclude(description__exact='')
    print(f"Checking {qs.count()} worlds...")
    
    count = 0
    for w in qs:
        pid = w.public_id
        is_valid = pid and len(pid) == 10 and re.match(r'^[A-Za-z0-9_-]+$', pid)
        
        # Also check if it looks like a JID (numeric or raw ID) or slug like "AbismoPrime"
        # If not valid NanoID format, regenerate.
        if not is_valid:
            new_id = generate_nanoid()
            w.public_id = new_id
            w.save()
            print(f"Migrated [{w.id}] {pid} -> {new_id}")
            count += 1
            
    print(f"Migration Complete. Updated {count} entities.")

if __name__ == "__main__":
    force_migrate()
