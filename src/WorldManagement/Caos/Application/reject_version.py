from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosNotification

class RejectVersionUseCase:
    """
    Caso de Uso responsable de rechazar o descartar una propuesta de cambio.
    El rechazo mueve la versión al estado 'REJECTED', sirviendo como una 
    eliminación lógica que permite conservar el historial de cambios descartados.
    """
    def execute(self, version_id: int, reason: str = "", reviewer=None):
        try:
            # Recuperar la propuesta desde el ORM
            version = CaosVersionORM.objects.get(id=version_id)
        except CaosVersionORM.DoesNotExist:
            raise Exception("La propuesta que intenta rechazar no existe.")

        # Regla de Negocio: Se pueden rechazar tanto las propuestas nuevas (PENDING) 
        # como las que ya habían sido aprobadas pero no publicadas aún (APPROVED).
        if version.status not in ["PENDING", "APPROVED"]:
            raise Exception(f"Operación denegada. No se puede rechazar una versión con estado final: {version.status}")

        # Pasamos la versión a REJECTED (estado de descarte)
        version.status = "REJECTED"
        
        # Almacenar el motivo del rechazo para dar feedback al proponente
        if reason:
            version.admin_feedback = reason

        if reviewer:
            version.reviewer = reviewer
            
        version.save()

        # Create Notification for the author
        if version.author:
            feedback_msg = f" Motivo: {reason}" if reason else ""
            CaosNotification.objects.create(
                user=version.author,
                title="❌ Propuesta Rechazada",
                message=f"Tu propuesta para '{version.world.name}' ha sido rechazada.{feedback_msg}",
                url=f"/dashboard/?type=WORLD"
            )
        
        print(f" ❌ Descartada propuesta v{version.version_number} para '{version.world.name}'.")
        if reason:
            print(f"    └── Feedback del Admin: {reason}")