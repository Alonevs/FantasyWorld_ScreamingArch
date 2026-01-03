from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM, CaosNotification

class ApproveNarrativeVersionUseCase:
    """
    Caso de Uso responsable de aprobar una propuesta de cambio en una narrativa.
    Al igual que con las entidades, la aprobación marca el contenido como 'visto bueno'
    por el administrador, permitiendo su posterior publicación al estado 'Live'.
    """
    def execute(self, version_id: int, reviewer=None):
        try:
            # Recuperar la propuesta de versión de narrativa
            version = CaosNarrativeVersionORM.objects.get(id=version_id)
            
            # Cambiar estado a APROBADA
            version.status = 'APPROVED'
            if reviewer:
                version.reviewer = reviewer
            version.save()
            
            # Create Notification for the author
            if version.author:
                CaosNotification.objects.create(
                    user=version.author,
                    title="📖 Lore Aprobado",
                    message=f"Tu propuesta de lore para '{version.narrative.titulo}' ha sido aprobada.",
                    url=f"/dashboard/?type=NARRATIVE"
                )
            
            print(f" ✅ Propuesta de lore v{version.version_number} APROBADA para '{version.narrative.titulo}'.")
            
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("La propuesta de narrativa no existe en el sistema.")
