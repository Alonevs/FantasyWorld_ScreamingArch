from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from django.contrib.auth.models import User

class ProposeChangeUseCase:
    def execute(self, world_id: str, new_name: str, new_desc: str, reason: str, user: User) -> int:
        try:
            world = CaosWorldORM.objects.get(id=world_id)
        except CaosWorldORM.DoesNotExist:
            raise Exception("Mundo no encontrado")

        last_ver = world.versiones.first()
        next_num = (last_ver.version_number + 1) if last_ver else 1

        # Guardamos con autor
        version = CaosVersionORM.objects.create(
            world=world,
            proposed_name=new_name,
            proposed_description=new_desc,
            version_number=next_num,
            status="PENDING",
            change_log=reason,
            author=user # <--- AQUÍ
        )
        
        print(f" 📝 Propuesta v{next_num} creada por {user.username}")
        return next_num