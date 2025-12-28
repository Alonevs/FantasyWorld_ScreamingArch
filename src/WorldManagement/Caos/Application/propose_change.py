from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from django.contrib.auth.models import User

class ProposeChangeUseCase:
    """
    Caso de Uso responsable de generar una propuesta de cambio (Snapshot).
    En lugar de editar la entidad en vivo, este proceso crea un registro de versión
    con el estado deseado. El cambio queda en espera (PENDING) hasta ser 
    revisado por un administrador.
    """
    def execute(self, world_id: str, new_name: str, new_desc: str, reason: str, user: User, metadata_proposal: dict = None) -> int:
        # 1. Recuperar la entidad desde la base de datos (Datos actuales 'Live')
        try:
            live_world = CaosWorldORM.objects.get(id=world_id)
        except CaosWorldORM.DoesNotExist:
            raise Exception("No se puede proponer cambios: La entidad no existe.")

        # 2. Determinar el siguiente número de versión secuencial
        last_ver = live_world.versiones.first()
        next_num = (last_ver.version_number + 1) if last_ver else 1

        # 3. Preparar la Copia de Datos (Snapshot)
        # Si no se proporciona un nuevo valor, se mantiene el actual para que la versión sea completa.
        final_name = new_name if new_name is not None else live_world.name
        final_desc = new_desc if new_desc is not None else live_world.description
        
        # Lógica de Metadatos: Almacenamos la estructura propuesta en el campo JSON 'cambios'
        changes_json = {}
        if metadata_proposal:
            changes_json['metadata'] = metadata_proposal
            changes_json['action'] = 'METADATA_UPDATE'

        if metadata_proposal and 'chronology' in metadata_proposal:
             parent_id = world_id[:-2]
             if len(parent_id) >= 2:
                 from src.WorldManagement.Caos.Domain.Services.temporal_validator import TemporalValidator, TemporalConsistencyError
                 try:
                     parent = CaosWorldORM.objects.get(id=parent_id)
                     validator = TemporalValidator()
                     # Validamos la Propuesta (Hijo) contra el Padre (Live)
                     validator.validate_consistency(metadata_proposal, parent.metadata)
                 except CaosWorldORM.DoesNotExist:
                     pass
                 except TemporalConsistencyError as e:
                     raise Exception(f"⛔ Error Temporal: {e}")

        # 4. Crear la Propuesta (Registro de Versión)
        # Este registro actúa como un "clon" del estado futuro deseado.
        version = CaosVersionORM.objects.create(
            world=live_world,
            proposed_name=final_name,
            proposed_description=final_desc,
            version_number=next_num,
            status="PENDING",
            change_log=reason,
            cambios=changes_json,
            author=user
        )
        
        print(f" 📝 Propuesta v{next_num} generada para '{live_world.name}'. Pendiente de revisión.")
        return next_num