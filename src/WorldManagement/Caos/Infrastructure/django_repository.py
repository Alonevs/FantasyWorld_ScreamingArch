import sys
from django.db.models import Max
from django.db.models.functions import Length
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Domain.entities import CaosWorld, VersionStatus
from src.Shared.Domain.value_objects import WorldID
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.Shared.Domain import eclai_core

class DjangoCaosRepository(CaosRepository):
    
    def save(self, world: CaosWorld):
        status_str = world.status.value if hasattr(world.status, 'value') else world.status
        CaosWorldORM.objects.update_or_create(
            id=world.id.value,
            defaults={
                'name': world.name,
                'description': world.lore_description,
                'status': status_str
            }
        )
        print(f" 💾 [DB] Guardado: {world.name} ({world.id.value})")

    def find_by_id(self, world_id: WorldID):
        try:
            orm_obj = CaosWorldORM.objects.get(id=world_id.value)
            return CaosWorld(
                id=WorldID(str(orm_obj.id)),
                name=orm_obj.name,
                lore_description=orm_obj.description,
                status=getattr(VersionStatus, orm_obj.status, VersionStatus.DRAFT)
            )
        except CaosWorldORM.DoesNotExist:
            return None

    def get_next_child_id(self, parent_id_str: str) -> str:
        # 1. Determinar nivel del padre y del hijo
        # Si parent="01" (len 2, Nivel 1) -> Hijo será Nivel 2
        len_parent = len(parent_id_str)
        nivel_padre = eclai_core.get_level_from_jid_length(len_parent)
        nivel_hijo = nivel_padre + 1
        
        # Calcular longitud esperada del hijo
        # Nivel 2 (Abismos) son 4 dígitos (Padre 2 + Hijo 2)
        # Nivel 17 (Entidad) son 36 dígitos
        if nivel_hijo == 17:
            len_hijo = len_parent + 4
        else:
            len_hijo = len_parent + 2

        # 2. Buscar en DB el último hijo existente
        # Filtramos por: Empieza con el ID del padre Y tiene la longitud correcta
        ultimo_hijo = CaosWorldORM.objects.filter(
            id__startswith=parent_id_str
        ).annotate(id_len=Length('id')).filter(
            id_len=len_hijo
        ).aggregate(Max('id'))['id__max']

        # 3. Calcular el siguiente secuencial
        if not ultimo_hijo:
            siguiente_seq = 1
        else:
            # Extraemos el segmento final (los últimos 2 o 4 dígitos)
            segmento = ultimo_hijo[len_parent:]
            siguiente_seq = int(segmento) + 1

        # 4. Formatear el nuevo segmento (rellenar con ceros)
        if nivel_hijo == 17:
            nuevo_segmento = f"{siguiente_seq:04d}"
        else:
            nuevo_segmento = f"{siguiente_seq:02d}"

        # 5. Construir ID completo usando tu motor ECLAI
        # Nota: eclai_core.construir_jid usa 'ruta_base' que es el ID del padre
        return eclai_core.construir_jid(parent_id_str, nivel_hijo, nuevo_segmento)