from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosNotification

class ApproveVersionUseCase:
    """
    Caso de Uso responsable de aprobar una propuesta de cambio (versión).
    Esta acción marca la versión como lista para ser publicada, pero NO altera 
    los datos 'Live' de la entidad hasta que se ejecute la publicación formal.
    """
    def execute(self, version_id: int, reviewer=None):
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
        if reviewer:
            version.reviewer = reviewer
        version.save()

        # Create Notification for the author
        if version.author:
            CaosNotification.objects.create(
                user=version.author,
                title="✅ Propuesta Aprobada",
                message=f"Tu propuesta para '{version.world.name}' ha sido aprobada.",
                url=f"/dashboard/?type=WORLD"
            )
        
        print(f" ✅ Propuesta v{version.version_number} APROBADA. Pendiente de paso a producción (Live).")