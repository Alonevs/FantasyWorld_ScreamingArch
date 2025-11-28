import os
import base64
from django.conf import settings
from django.db.models import Max
from django.db.models.functions import Length

from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Domain.entities import CaosWorld, VersionStatus
from src.WorldManagement.Caos.Domain.creature import Creature
from src.Shared.Domain.value_objects import WorldID
from src.Shared.Domain import eclai_core
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

class DjangoCaosRepository(CaosRepository):
    
    def save(self, world: CaosWorld):
        status_str = world.status.value if hasattr(world.status, 'value') else world.status
        CaosWorldORM.objects.update_or_create(
            id=world.id.value,
            defaults={
                'name': world.name,
                'description': world.lore_description,
                'status': status_str,
                'metadata': world.metadata
            }
        )
        print(f" 💾 [DB] Guardado: {world.name}")

    def find_by_id(self, world_id):
        val = world_id.value if hasattr(world_id, 'value') else world_id
        try:
            orm_obj = CaosWorldORM.objects.get(id=val)
            return CaosWorld(
                id=WorldID(str(orm_obj.id)),
                name=orm_obj.name,
                lore_description=orm_obj.description,
                status=getattr(VersionStatus, orm_obj.status, VersionStatus.DRAFT),
                metadata=orm_obj.metadata or {}
            )
        except CaosWorldORM.DoesNotExist:
            return None

    # --- MÉTODOS DE CRIATURAS ---
    def save_creature(self, creature: Creature):
        CaosWorldORM.objects.update_or_create(
            id=creature.eclai_id,
            defaults={
                'name': creature.name,
                'description': creature.description,
                'metadata': creature.to_metadata_dict(),
                'status': 'DRAFT',
                'current_version_number': 1,
                'current_author_name': 'AI_Genesis',
                'id_codificado': eclai_core.encode_eclai126(creature.eclai_id)
            }
        )
        print(f" 🧬 [DB] Criatura guardada: {creature.name}")

    def save_image(self, jid: str, base64_data: str):
        if not base64_data: return
        base_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
        target_dir = os.path.join(base_dir, jid)
        os.makedirs(target_dir, exist_ok=True)
        filename = f"{jid}_v1.png"
        file_path = os.path.join(target_dir, filename)
        try:
            if "," in base64_data: base64_data = base64_data.split(",")[1]
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(base64_data))
            print(f" 🎨 [FS] Imagen guardada: {filename}")
        except Exception as e:
            print(f"⚠️ Error guardando imagen: {e}")

    def get_next_child_id(self, parent_id_str: str) -> str:
        len_parent = len(parent_id_str)
        nivel_padre = eclai_core.get_level_from_jid_length(len_parent)
        nivel_hijo = nivel_padre + 1
        es_entidad = (nivel_hijo == 16) 
        len_hijo = 34 if es_entidad else len_parent + 2

        ultimo_hijo = CaosWorldORM.objects.filter(
            id__startswith=parent_id_str
        ).annotate(id_len=Length('id')).filter(
            id_len=len_hijo
        ).aggregate(Max('id'))['id__max']

        if not ultimo_hijo:
            siguiente_seq = 1
        else:
            cut = 4 if es_entidad else 2
            segmento = ultimo_hijo[-cut:]
            siguiente_seq = int(segmento) + 1

        if es_entidad: nuevo_segmento = f"{siguiente_seq:04d}"
        else: nuevo_segmento = f"{siguiente_seq:02d}"

        return eclai_core.construir_jid(parent_id_str, nivel_hijo, nuevo_segmento)
