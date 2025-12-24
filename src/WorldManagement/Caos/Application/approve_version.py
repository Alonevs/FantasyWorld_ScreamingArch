from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM

class ApproveVersionUseCase:
    """
    Caso de Uso responsable de aprobar una propuesta de cambio (versión).
    Esta acción marca la versión como lista para ser publicada, pero NO altera 
    los datos 'Live' de la entidad hasta que se ejecute la publicación formal.
    """
    def execute(self, version_id: int):
        try:
            # Recuperar la versión desde la persistencia
            version = CaosVersionORM.objects.get(id=version_id)
        except CaosVersionORM.DoesNotExist:
            raise Exception("La versión especificada no existe en el sistema.")

        # Regla de Negocio: Solo se pueden aprobar elementos en espera de revisión
        if version.status != "PENDING":
            raise Exception(f"No se puede aprobar esta versión. El estado actual es: {version.status}")

        # La aprobación es un paso intermedio. 
        # Marca la transición de PENDING -> APPROVED.
        version.status = "APPROVED"
        version.save()
        
        print(f" ✅ Propuesta v{version.version_number} APROBADA. Pendiente de paso a producción (Live).")