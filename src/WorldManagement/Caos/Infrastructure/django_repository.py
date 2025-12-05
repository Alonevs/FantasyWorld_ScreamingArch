import os
import base64
import io
import time
from typing import List, Optional
from datetime import datetime
from PIL import Image
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
        
        # Handle Locking Logic mapping to Status
        if world.is_locked:
            status_str = 'LOCKED'
        elif status_str == 'LOCKED':
            # If unlocked but status says LOCKED, revert to DRAFT
            status_str = 'DRAFT'

        CaosWorldORM.objects.update_or_create(
            id=world.id.value,
            defaults={
                'name': world.name,
                'description': world.lore_description,
                'status': status_str,
                'metadata': world.metadata,
                'visible_publico': world.is_public
                # Removed 'is_locked' as it is a property, not a field
            }
        )
        print(f" 💾 [DB] Guardado: {world.name}")

    def find_by_id(self, world_id) -> Optional[CaosWorld]:
        val = world_id.value if hasattr(world_id, 'value') else world_id
        try:
            orm_obj = CaosWorldORM.objects.get(id=val)
            return CaosWorld(
                id=WorldID(str(orm_obj.id)),
                name=orm_obj.name,
                lore_description=orm_obj.description,
                status=getattr(VersionStatus, orm_obj.status, VersionStatus.DRAFT),
                metadata=orm_obj.metadata or {},
                is_public=orm_obj.visible_publico,
                is_locked=orm_obj.is_locked
            )
        except CaosWorldORM.DoesNotExist:
            return None

    def get_by_public_id(self, public_id: str) -> Optional[CaosWorld]:
        try:
            orm_obj = CaosWorldORM.objects.get(public_id=public_id)
            return CaosWorld(
                id=WorldID(str(orm_obj.id)),
                name=orm_obj.name,
                lore_description=orm_obj.description,
                status=getattr(VersionStatus, orm_obj.status, VersionStatus.DRAFT),
                metadata=orm_obj.metadata or {},
                is_public=orm_obj.visible_publico,
                is_locked=orm_obj.is_locked
            )
        except CaosWorldORM.DoesNotExist:
            return None

    def find_descendants(self, root_id: WorldID) -> List[CaosWorld]:
        root_val = root_id.value if hasattr(root_id, 'value') else root_id
        # Filter by startswith and order by ID to maintain hierarchy
        orm_objs = CaosWorldORM.objects.filter(id__startswith=root_val).order_by('id')
        results = []
        for obj in orm_objs:
            results.append(CaosWorld(
                id=WorldID(str(obj.id)),
                name=obj.name,
                lore_description=obj.description,
                status=getattr(VersionStatus, obj.status, VersionStatus.DRAFT),
                metadata=obj.metadata or {},
                is_public=obj.visible_publico,
                is_locked=obj.is_locked
            ))
        return results

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

    def _inject_metadata(self, image, artist="ECLAI User"):
        try:
            exif = image.getexif()
            # 0x013b: Artist, 0x0131: Software, 0x0132: DateTime
            exif[0x013b] = artist
            exif[0x0131] = "ECLAI World Builder v4.9"
            exif[0x0132] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return exif
        except:
            return image.getexif()

    def _audit_log(self, jid, filename, uploader, origin, title=None):
        try:
            world = CaosWorldORM.objects.get(id=jid)
            if not world.metadata: world.metadata = {}
            if 'gallery_log' not in world.metadata: world.metadata['gallery_log'] = {}
            
            world.metadata['gallery_log'][filename] = {
                "uploader": uploader,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "origin": origin,
                "title": title or "Sin Título"
            }
            world.save()
        except Exception as e:
            print(f"⚠️ Error auditoría: {e}")

    def update_image_metadata(self, jid, filename, new_title):
        try:
            world = CaosWorldORM.objects.get(id=jid)
            if not world.metadata: return False
            if 'gallery_log' not in world.metadata: return False
            
            # Buscamos la entrada de la imagen
            if filename in world.metadata['gallery_log']:
                world.metadata['gallery_log'][filename]['title'] = new_title
                world.save()
                print(f" ✏️ [Metadata] Título actualizado para {filename}: {new_title}")
                return True
            return False
        except Exception as e:
            print(f"⚠️ Error actualizando metadata: {e}")
            return False

    def save_image(self, jid, base64_data, title=None, username="AI System"):
        if not base64_data: return None
        base_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
        target_dir = os.path.join(base_dir, jid)
        os.makedirs(target_dir, exist_ok=True)
        timestamp = int(time.time())
        filename = f"{jid}_ia_{timestamp}.webp"
        file_path = os.path.join(target_dir, filename)

        try:
            if "," in base64_data: base64_data = base64_data.split(",")[1]
            image = Image.open(io.BytesIO(base64.b64decode(base64_data)))
            exif = self._inject_metadata(image, artist=username)
            image.save(file_path, "WEBP", quality=85, exif=exif)
            self._audit_log(jid, filename, username, "GENERATED", title=title)
            return filename
        except Exception as e:
            print(f"⚠️ Error IA save: {e}")
            return None

    def save_manual_file(self, jid, uploaded_file, username="Unknown", title=None):
        base_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
        target_dir = os.path.join(base_dir, jid)
        os.makedirs(target_dir, exist_ok=True)

        # Determinar nombre
        raw_name = title if title else f"{jid}_m_{int(time.time())}"
        safe_name = "".join([c for c in raw_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        if not safe_name: safe_name = "imagen"

        # Anti-Colisión
        filename = f"{safe_name}.webp"
        counter = 1
        while os.path.exists(os.path.join(target_dir, filename)):
            filename = f"{safe_name}_{counter}.webp"
            counter += 1
            
        file_path = os.path.join(target_dir, filename)

        try:
            image = Image.open(uploaded_file)
            if image.mode in ("RGBA", "P"): image = image.convert("RGB")
            exif = self._inject_metadata(image, artist=username)
            image.save(file_path, "WEBP", quality=90, exif=exif)
            self._audit_log(jid, filename, username, "MANUAL_UPLOAD", title=title)
            print(f" 📎 [Upload] Guardado: {filename}")
            return True
        except Exception as e:
            print(f"⚠️ Error manual save: {e}")
            return False

    def get_next_child_id(self, parent_id_str: str) -> str:
        len_parent = len(parent_id_str)
        nivel_padre = eclai_core.get_level_from_jid_length(len_parent)
        nivel_hijo = nivel_padre + 1
        es_entidad = (nivel_hijo == 16) 
        len_hijo = 34 if es_entidad else len_parent + 2

        ultimo_hijo = CaosWorldORM.objects.filter(id__startswith=parent_id_str).annotate(id_len=Length('id')).filter(id_len=len_hijo).aggregate(Max('id'))['id__max']

        if not ultimo_hijo: siguiente_seq = 1
        else:
            cut = 4 if es_entidad else 2
            segmento = ultimo_hijo[-cut:]
            siguiente_seq = int(segmento) + 1

        if es_entidad: nuevo_segmento = f"{siguiente_seq:04d}"
        else: nuevo_segmento = f"{siguiente_seq:02d}"

        return eclai_core.construir_jid(parent_id_str, nivel_hijo, nuevo_segmento)

    def get_next_narrative_id(self, prefix: str) -> str:
        from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM
        existing_nids = CaosNarrativeORM.objects.filter(nid__startswith=prefix).values_list('nid', flat=True)
        used_nums = set()
        len_prefix = len(prefix)
        for nid_str in existing_nids:
            try:
                suffix = nid_str[len_prefix:]
                if suffix.isdigit(): used_nums.add(int(suffix))
            except: pass
        next_num = 1
        while next_num in used_nums: next_num += 1
        return f"{prefix}{next_num:02d}"
