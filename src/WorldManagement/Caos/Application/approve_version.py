from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM

class ApproveVersionUseCase:
    def execute(self, version_id: int):
        try:
            version = CaosVersionORM.objects.get(id=version_id)
        except CaosVersionORM.DoesNotExist:
            raise Exception("Versión no encontrada")

        if version.status != "PENDING":
            raise Exception(f"Solo se pueden aprobar pendientes. Estado actual: {version.status}")

        # SOLO CAMBIAMOS EL ESTADO (No tocamos el Live)
        version.status = "APPROVED"
        version.save()
        
        print(f" ✅ Versión {version.version_number} APROBADA (Esperando publicación).")