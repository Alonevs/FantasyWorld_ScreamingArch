import sys
# Importamos la interfaz y la entidad pura
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Domain.entities import CaosWorld, VersionStatus
from src.Shared.Domain.value_objects import WorldID

# OJO: Los modelos de Django se importan DENTRO de los métodos o después del setup en main
# para evitar errores de "App not ready".
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

class DjangoCaosRepository(CaosRepository):
    """
    Implementación del Repositorio de Caos usando Django ORM.
    
    Esta clase actúa como un adaptador entre el Dominio (Entities) y la Infraestructura (Django Models).
    Se encarga de:
    1. Mapear Entidades de Dominio -> Modelos de Django (al guardar).
    2. Mapear Modelos de Django -> Entidades de Dominio (al leer).
    """
    
    def save(self, world: CaosWorld):
        """
        Guarda o actualiza un mundo en la base de datos SQL.
        
        Args:
            world (CaosWorld): La entidad de dominio a persistir.
        """
        # Convertimos Enum a string para guardarlo
        status_str = world.status.value if hasattr(world.status, 'value') else world.status

        # Guardamos en la DB real usando el ORM
        CaosWorldORM.objects.update_or_create(
            id=world.id.value,
            defaults={
                'name': world.name,
                'description': world.lore_description,
                'status': status_str
            }
        )
        print(f" 💾 [DJANGO SQL] Guardado en db.sqlite3: {world.name}")

    def find_by_id(self, world_id: WorldID):
        """
        Busca un mundo por su ID.
        
        Args:
            world_id (WorldID): Value Object con el ID a buscar.
            
        Returns:
            CaosWorld | None: La entidad reconstituida o None si no existe.
        """
        try:
            orm_obj = CaosWorldORM.objects.get(id=world_id.value)
            # Reconstruimos la entidad pura
            # (Aquí tendrías que mapear el string 'DRAFT' de vuelta al Enum, lo simplifico por ahora)
            return CaosWorld(
                id=WorldID(str(orm_obj.id)),
                name=orm_obj.name,
                lore_description=orm_obj.description,
                status=getattr(VersionStatus, orm_obj.status, VersionStatus.DRAFT)
            )
        except CaosWorldORM.DoesNotExist:
            return None