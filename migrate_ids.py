
import nanoid
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def generate_nanoid():
    return nanoid.generate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-', 10)

def migrate_ids():
    ids = ["0101", "010102", "010104"]
    for i in ids:
        try:
            w = CaosWorldORM.objects.get(id=i)
            old_pid = w.public_id
            new_pid = generate_nanoid()
            
            w.public_id = new_pid
            # Clear id_codificado if user says it's not used, or keep it as legacy. 
            # User said "arreglalo para que se vea con su id correcto", implying public_id is the "correct" one now.
            # I will leave id_codificado alone or clear it if needed, but primary goal is public_id.
            
            w.save()
            print(f"[{i}] {w.name}")
            print(f"    Old Public ID: {old_pid}")
            print(f"    New Public ID: {new_pid}")
            print(f"    URL: /mundo/{new_pid}/")
            
        except CaosWorldORM.DoesNotExist:
            print(f"[{i}] Not found.")

if __name__ == "__main__":
    migrate_ids()
