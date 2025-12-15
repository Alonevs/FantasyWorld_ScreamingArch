
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def show():
    with open('new_ids.txt', 'w', encoding='utf-8') as f:
        ids = ["0101", "010102", "010104"]
        for i in ids:
            try:
                w = CaosWorldORM.objects.get(id=i)
                f.write(f"{w.name} | {w.public_id}\n")
            except:
                f.write(f"{i} | NOT FOUND\n")

if __name__ == "__main__":
    show()
