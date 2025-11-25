from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM

class RejectVersionUseCase:
    def execute(self, version_id: int):
        try:
            version = CaosVersionORM.objects.get(id=version_id)
        except CaosVersionORM.DoesNotExist:
            raise Exception("Versión no encontrada")

        if version.status != "PENDING":
            raise Exception(f"No se puede rechazar una versión en estado {version.status}")

        # Simplemente cambiamos el estado a REJECTED
        version.status = "REJECTED"
        version.save()
        
        print(f" ❌ Rechazada propuesta v{version.version_number} para '{version.world.name}'.")