from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from django.contrib.auth.models import User

class ProposeChangeUseCase:
    def execute(self, world_id: str, new_name: str, new_desc: str, reason: str, user: User) -> int:
        # 1. Recuperar la "Verdad Absoluta" (Datos actuales en Live)
        try:
            live_world = CaosWorldORM.objects.get(id=world_id)
        except CaosWorldORM.DoesNotExist:
            raise Exception("Mundo no encontrado")

        # 2. Calcular siguiente número de versión
        last_ver = live_world.versiones.first()
        next_num = (last_ver.version_number + 1) if last_ver else 1

        # 3. ESTRATEGIA DE COPIA SEGURA (SNAPSHOT)
        # Si el formulario no envía un dato (es None o vacío), MANTENEMOS el dato viejo.
        # Esto evita borrar datos accidentalmente si el formulario está incompleto.
        
        final_name = new_name if new_name is not None else live_world.name
        final_desc = new_desc if new_desc is not None else live_world.description
        
        # (En el futuro, aquí añadirías: final_poblacion = new_pob or live_world.poblacion)

        # 4. Crear la Versión (Es una copia completa del estado deseado)
        version = CaosVersionORM.objects.create(
            world=live_world,
            proposed_name=final_name,          # Guardamos la fusión
            proposed_description=final_desc,   # Guardamos la fusión
            version_number=next_num,
            status="PENDING",
            change_log=reason,
            author=user
        )
        
        print(f" 📝 Propuesta v{next_num} generada (Copia segura de '{live_world.name}').")
        return next_num