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
from src.Shared.Domain import id_utils

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

class DjangoCaosRepository(CaosRepository):
    """
    Implementación concreta del repositorio utilizando el ORM de Django.
    Esta clase actúa como el Adaptador de Infraestructura que comunica el Dominio 
    con la base de datos SQL y el sistema de archivos (para imágenes).
    """
    
    def save(self, world: CaosWorld):
        """
        Sincroniza el estado de una entidad del dominio con la base de datos.
        Gestiona la lógica de mapeo de estados, incluyendo el soporte para bloqueos.
        """
        status_str = world.status.value if hasattr(world.status, 'value') else world.status
        
        # Lógica de Bloqueo: Si la entidad está marcada como bloqueada, 
        # su estado en DB se fuerza a 'LOCKED'.
        if world.is_locked:
            status_str = 'LOCKED'
        elif status_str == 'LOCKED':
            # Si se desbloquea pero el estado persistido era LOCKED, vuelve a DRAFT por seguridad.
            status_str = 'DRAFT'

        CaosWorldORM.objects.update_or_create(
            id=world.id.value,
            defaults={
                'name': world.name,
                'description': world.lore_description,
                'status': status_str,
                'metadata': world.metadata,
                'visible_publico': world.is_public
                # Nota: 'is_locked' es una propiedad calculada en el ORM basada en el estado.
            }
        )
        print(f" 💾 [Persistencia] Entidad '{world.name}' guardada en base de datos.")

    def _to_domain(self, orm_obj: CaosWorldORM) -> CaosWorld:
        """Maquetador de objetos ORM a Entidades de Dominio puras."""
        return CaosWorld(
            id=WorldID(str(orm_obj.id)),
            name=orm_obj.name,
            lore_description=orm_obj.description or "",
            status=getattr(VersionStatus, orm_obj.status, VersionStatus.DRAFT),
            metadata=orm_obj.metadata or {},
            is_public=orm_obj.visible_publico,
            is_locked=orm_obj.is_locked
        )

    def find_by_id(self, world_id) -> Optional[CaosWorld]:
        """Recupera una entidad activa por su J-ID."""
        val = world_id.value if hasattr(world_id, 'value') else world_id
        try:
            orm_obj = CaosWorldORM.objects.get(id=val, is_active=True)
            return self._to_domain(orm_obj)
        except CaosWorldORM.DoesNotExist:
            return None

    def get_by_public_id(self, public_id: str) -> Optional[CaosWorld]:
        """Recupera una entidad activa por su NanoID público."""
        try:
            orm_obj = CaosWorldORM.objects.get(public_id=public_id, is_active=True)
            return self._to_domain(orm_obj)
        except CaosWorldORM.DoesNotExist:
            return None

    def find_descendants(self, root_id: WorldID) -> List[CaosWorld]:
        """Recupera todos los descendientes lógicos de una rama jerárquica."""
        root_val = root_id.value if hasattr(root_id, 'value') else root_id
        orm_objs = CaosWorldORM.objects.filter(id__startswith=root_val, is_active=True).order_by('id')
        return [self._to_domain(obj) for obj in orm_objs]

    def get_ancestors_by_id(self, entity_id: str) -> List[CaosWorld]:
        """Recupera la línea ascendente (Padres, Abuelos) de una entidad."""
        ids_to_fetch = []
        # Generar IDs de ancestros cortando el J-ID actual en segmentos de 2
        for l in range(2, len(entity_id), 2):
            ids_to_fetch.append(entity_id[:l])
            
        if not ids_to_fetch:
            return []
            
        orm_objs = CaosWorldORM.objects.filter(id__in=ids_to_fetch, is_active=True).order_by('id')
        return [self._to_domain(obj) for obj in orm_objs]

    def save_creature(self, creature: Creature):
        """Persiste una entidad de tipo Criatura generada por IA."""
        CaosWorldORM.objects.update_or_create(
            id=creature.id.value,
            defaults={
                'name': creature.name,
                'description': creature.description,
                'metadata': creature.to_metadata_dict(),
                'status': 'DRAFT',
                'current_version_number': 1,
                'current_author_name': 'IA_Genesis'
            }
        )
        print(f" 🧬 [Persistencia] Criatura '{creature.name}' guardada.")

    # --- Gestión de Archivos e Imágenes ---

    def _inject_metadata(self, image, artist="ECLAI User"):
        """Inyecta metadatos EXIF de autoría y software en la imagen generada."""
        try:
            exif = image.getexif()
            exif[0x013b] = artist # Artista
            exif[0x0131] = "ECLAI World Builder v4.9" # Software
            exif[0x0132] = datetime.now().strftime("%d/%m/%Y") # Timestamp
            return exif
        except:
            return image.getexif()

    def _audit_log(self, jid, filename, uploader, origin, title=None, period_slug=None):
        """Registra el historial de subida de una imagen en los metadatos de la entidad."""
        try:
            world = CaosWorldORM.objects.get(id=jid)
            if not world.metadata: world.metadata = {}
            if 'gallery_log' not in world.metadata: world.metadata['gallery_log'] = {}
            
            world.metadata['gallery_log'][filename] = {
                "uploader": uploader,
                "date": datetime.now().strftime("%d/%m/%Y"),
                "origin": origin,
                "title": title or "Sin Título",
                "period": period_slug # Nulo = ACTUAL
            }
            world.save()
        except Exception as e:
            print(f"⚠️ Error en auditoría de galería: {e}")

    def save_image(self, jid, base64_data, title=None, username="AI System", period_slug=None):
        """Guarda una imagen generada por IA en el sistema de archivos y registra el log."""
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
            # Guardamos en formato WEBP optimizado
            image.save(file_path, "WEBP", quality=85, exif=exif)
            self._audit_log(jid, filename, username, "GENERATED", title=title, period_slug=period_slug)
            return filename
        except Exception as e:
            print(f"⚠️ Error al guardar imagen de IA: {e}")
            return None

    def save_manual_file(self, jid, uploaded_file, username="Unknown", title=None, period_slug=None):
        """Gestiona la subida manual de archivos de imagen por parte de un usuario."""
        base_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
        target_dir = os.path.join(base_dir, jid)
        os.makedirs(target_dir, exist_ok=True)

        # Sanitización de nombre de archivo
        raw_name = title if title else f"{jid}_m_{int(time.time())}"
        safe_name = "".join([c for c in raw_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        if not safe_name: safe_name = "imagen"

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
            self._audit_log(jid, filename, username, "MANUAL_UPLOAD", title=title, period_slug=period_slug)
            print(f" 📎 [Upload] Archivo '{filename}' subido y procesado.")
            return True
        except Exception as e:
            print(f"⚠️ Error al guardar archivo manual: {e}")
            return False

    # --- Lógica Avanzada de Identificadores (J-ID) ---

    def get_next_child_id(self, parent_id_str: str, target_level: int = None) -> str:
        """
        Calcula el siguiente J-ID disponible, soportando lógica de saltos (Gaps).
        Busca 'huecos' en la jerarquía para asignar el menor número disponible.
        """
        nivel_padre = id_utils.get_level_u(parent_id_str)
        nivel_hijo = target_level if target_level else nivel_padre + 1
        
        # Determinamos cuántos niveles de salto (Gaps) hay
        gaps = nivel_hijo - nivel_padre - 1
        
        # Las entidades finales (Nivel 16) usan 4 dígitos, el resto 2.
        es_entidad = (nivel_hijo == 16)
        segment_len = 4 if es_entidad else 2
        
        # Los saltos se representan con '00' en el ID
        padding = "00" * gaps if gaps > 0 else ""
        prefix = parent_id_str + padding
        
        target_len = len(prefix) + segment_len
        
        # Recuperamos hermanos existentes en el mismo nivel exacto
        siblings = CaosWorldORM.objects.filter(id__startswith=prefix).annotate(id_len=Length('id')).filter(id_len=target_len).values_list('id', flat=True)
        
        existing_nums = set()
        for s_id in siblings:
            try:
                seg = s_id[-segment_len:]
                existing_nums.add(int(seg))
            except: pass
            
        # Algoritmo de Gap Filling: Buscar el primer número natural saltado.
        siguiente_seq = 1
        while siguiente_seq in existing_nums:
            siguiente_seq += 1

        nuevo_segmento = f"{siguiente_seq:0{segment_len}d}"
        return prefix + nuevo_segmento

    def get_next_narrative_id(self, prefix: str) -> str:
        """Genera el siguiente NID jerárquico para una narrativa/capítulo."""
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

    def get_visited_narrative_ids(self, user) -> set:
        """Recupera los IDs de narrativas visitadas por el usuario."""
        if not user or not user.is_authenticated:
            return set()
        
        from src.Infrastructure.DjangoFramework.persistence.models import CaosEventLog
        return set(CaosEventLog.objects.filter(
            user=user, 
            action='VIEW_NARRATIVE'
        ).values_list('target_id', flat=True))
