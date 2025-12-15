
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def fix_active():
    ids = ["010102", "010104"]
    for i in ids:
        try:
            w = CaosWorldORM.objects.get(id=i)
            print(f"[{i}] Before: is_active={w.is_active}")
            w.is_active = True
            w.deleted_at = None
            w.status = "LIVE" # Enforce LIVE just in case
            w.save()
            print(f"[{i}] After: is_active={w.is_active}")
        except CaosWorldORM.DoesNotExist:
            print(f"[{i}] Not found")

if __name__ == "__main__":
    fix_active()
