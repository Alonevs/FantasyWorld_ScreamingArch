from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM

class RejectVersionUseCase:
    def execute(self, version_id: int):
        try:
            version = CaosVersionORM.objects.get(id=version_id)
        except CaosVersionORM.DoesNotExist:
            raise Exception("Versión no encontrada")

        # CAMBIO: Ahora permitimos rechazar PENDING y APPROVED
        if version.status not in ["PENDING", "APPROVED"]:
            raise Exception(f"No se puede rechazar una versión en estado {version.status}")

        # Cambiamos el estado a REJECTED (Papelera)
        version.status = "REJECTED"
        version.save()
        
        print(f" ❌ Rechazada/Descartada propuesta v{version.version_number} para '{version.world.name}'.")