
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def restore():
    try:
        parent = CaosWorldORM.objects.get(id="0101")
        print(f"Parent found: {parent.name}")
    except CaosWorldORM.DoesNotExist:
        print("Parent 0101 not found! Cannot restore children.")
        return

    # Child 1: 010102
    c1, created1 = CaosWorldORM.objects.get_or_create(
        id="010102",
        defaults={
            "name": "Profundidad Carmesí [Recuperado]",
            "description": "Una vasta extensión de neblina roja donde la gravedad parece invertirse. Recuperado de los registros de eventos.",
            "status": "LIVE",
            "visible_publico": True,
            "public_id": "ProfundidadRed"
        }
    )
    if not created1:
        c1.status = "LIVE"
        c1.visible_publico = True
        c1.save()
    print(f"Restored: {c1.name} ({c1.id})")

    # Child 2: 010104
    c2, created2 = CaosWorldORM.objects.get_or_create(
        id="010104",
        defaults={
            "name": "Nexo del Vacío [Recuperado]",
            "description": "Punto de convergencia de energías oscuras. La realidad aquí es delgada como el papel. Datos reconstruidos.",
            "status": "LIVE",
            "visible_publico": True,
            "public_id": "NexoVacio"
        }
    )
    if not created2:
        c2.status = "LIVE"
        c2.visible_publico = True
        c2.save()
    print(f"Restored: {c2.name} ({c2.id})")

if __name__ == "__main__":
    restore()
