from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM

class ApproveNarrativeVersionUseCase:
    """
    Caso de Uso responsable de aprobar una propuesta de cambio en una narrativa.
    Al igual que con las entidades, la aprobación marca el contenido como 'visto bueno'
    por el administrador, permitiendo su posterior publicación al estado 'Live'.
    """
    def execute(self, version_id: int):
        try:
            # Recuperar la propuesta de versión de narrativa
            version = CaosNarrativeVersionORM.objects.get(id=version_id)
            
            # Regla de Negocio: Seguridad del flujo de revisión.
            if version.status != 'PENDING':
                raise Exception(f"No se puede aprobar. El estado actual es {version.status}, se requiere PENDING.")
            
            # Cambiar estado a APROBADO
            version.status = 'APPROVED'
            version.save()
            
            print(f" ✅ Propuesta de lore v{version.version_number} APROBADA para '{version.narrative.title}'.")
            
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("La propuesta de narrativa no existe en el sistema.")
