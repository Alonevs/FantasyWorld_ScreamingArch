import os
import base64
import io
import time
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


    def _inject_metadata(self, image, artist="ECLAI User"):
        """Inyecta metadatos EXIF básicos en la imagen."""
        try:
            from PIL.ExifTags import TAGS
            
            # Obtener objeto EXIF o crear uno nuevo
            exif = image.getexif()
            
            # IDs de tags estándar (Artist: 0x013b, Software: 0x0131, Copyright: 0x8298, DateTime: 0x0132)
            # Nota: Pillow maneja esto a bajo nivel
            exif[0x013b] = artist
            exif[0x0131] = "ECLAI World Builder v4.8"
            exif[0x8298] = "Project Internal Use"
            exif[0x0132] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return exif
        except Exception as e:
            print(f"⚠️ No se pudo inyectar EXIF: {e}")
            return image.getexif() # Devolver original si falla

    def _audit_log(self, jid, filename, uploader, origin):
        """Registra la imagen en el JSON del mundo."""
        try:
            world = CaosWorldORM.objects.get(id=jid)
            if not world.metadata: world.metadata = {}
            if 'gallery_log' not in world.metadata: world.metadata['gallery_log'] = {}
            
            world.metadata['gallery_log'][filename] = {
                "uploader": uploader,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "origin": origin
            }
            world.save()
        except Exception as e:
            print(f"⚠️ Error auditoría: {e}")

    def save_image(self, jid: str, base64_data: str):
        """Guarda imagen IA (WebP + Metadatos + Auditoría)."""
        if not base64_data: return
        base_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
        target_dir = os.path.join(base_dir, jid)
        os.makedirs(target_dir, exist_ok=True)
        
        # Usar timestamp para evitar cachés y colisiones
        timestamp = int(time.time())
        filename = f"{jid}_ia_{timestamp}.webp"
        file_path = os.path.join(target_dir, filename)

        try:
            if "," in base64_data: base64_data = base64_data.split(",")[1]
            image = Image.open(io.BytesIO(base64.b64decode(base64_data)))
            
            # Inyectar Firma
            exif_data = self._inject_metadata(image, artist="AI Generation")
            
            image.save(file_path, "WEBP", quality=85, exif=exif_data)
            self._audit_log(jid, filename, "AI System", "GENERATED")
            print(f" 🎨 [FS] Imagen IA firmada y guardada: {filename}")
            
        except Exception as e:
            print(f"⚠️ Error guardando imagen IA: {e}")

    def save_manual_file(self, jid: str, uploaded_file, username: str = "Unknown"):
        """Guarda imagen manual (WebP + Preservar/Inyectar + Auditoría)."""
        base_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
        target_dir = os.path.join(base_dir, jid)
        os.makedirs(target_dir, exist_ok=True)

        timestamp = int(time.time())
        filename = f"{jid}_m_{timestamp}.webp"
        file_path = os.path.join(target_dir, filename)

        try:
            image = Image.open(uploaded_file)
            if image.mode in ("RGBA", "P"): image = image.convert("RGB")
            
            # Si ya trae EXIF, lo mantenemos. Si no, le ponemos el nuestro.
            exif_data = image.info.get('exif')
            if not exif_data:
                exif_data = self._inject_metadata(image, artist=username)
            
            image.save(file_path, "WEBP", quality=90, exif=exif_data)
            self._audit_log(jid, filename, username, "MANUAL_UPLOAD")
            print(f" 📎 [Upload] Imagen manual firmada y guardada: {filename}")
            return True
        except Exception as e:
            print(f"⚠️ Error crítico subida manual: {e}")
            return False


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
