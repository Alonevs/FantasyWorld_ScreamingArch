from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from django.contrib.auth.models import User

class ProposeChangeUseCase:
    def execute(self, world_id: str, new_name: str, new_desc: str, reason: str, user: User, metadata_proposal: dict = None) -> int:
        # 1. Recuperar la "Verdad Absoluta" (Datos actuales en Live)
        try:
            live_world = CaosWorldORM.objects.get(id=world_id)
        except CaosWorldORM.DoesNotExist:
            raise Exception("Mundo no encontrado")

        # 2. Calcular siguiente número de versión
        last_ver = live_world.versiones.first()
        next_num = (last_ver.version_number + 1) if last_ver else 1

        # 3. ESTRATEGIA DE COPIA SEGURA (SNAPSHOT)
        final_name = new_name if new_name is not None else live_world.name
        final_desc = new_desc if new_desc is not None else live_world.description
        
        # Metadata logic: If proposed, use it. Else, keep existing (not exactly clean, but safe)
        # However, for metadata we usually want to store the DIFF or the FULL NEW STATE in 'cambios' 
        # for approval. Here we store the proposal in 'cambios' JSON.
        
        changes_json = {}
        if metadata_proposal:
            changes_json['metadata'] = metadata_proposal
            changes_json['action'] = 'METADATA_UPDATE'

        # 4. Crear la Versión (Es una copia completa del estado deseado)
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
        
        print(f" 📝 Propuesta v{next_num} generada (Copia segura de '{live_world.name}').")
        return next_num