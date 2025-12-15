
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.Shared.Domain import eclai_core

def update_codes():
    ids = ["0101", "010102", "010104"]
    for i in ids:
        try:
            w = CaosWorldORM.objects.get(id=i)
            expected = eclai_core.encode_eclai126(i)
            print(f"[{i}] Current: {w.id_codificado} | Expected: {expected}")
            
            if w.id_codificado != expected:
                w.id_codificado = expected
                w.save()
                print(f"[{i}] UPDATED.")
            else:
                print(f"[{i}] MATCH.")
                
        except CaosWorldORM.DoesNotExist:
            print(f"[{i}] Not found.")

if __name__ == "__main__":
    update_codes()
