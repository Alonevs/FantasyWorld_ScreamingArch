from django.db.models import Q
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

class StructuralSearchUseCase:
    """
    Caso de Uso para Búsqueda Semántica y Estructural.
    Combina filtrado jerárquico (J-ID Prefix) con consultas profundas en JSONB (Index GIN).
    """

    def execute(self, container_jid: str, filters: dict):
        """
        :param container_jid: J-ID del contenedor (ej: Galaxia '010304').
        :param filters: Diccionario de filtros flat (ej: {'gravedad__gte': 1.0, 'clima': 'arido'})
        :return: QuerySet o Lista de resultados
        """
        
        # 1. Base Query: Jerarquía y Estado Activo
        # Eficiencia: id__startswith usa el índice B-Tree de la Primary Key
        query = CaosWorldORM.objects.filter(
            id__startswith=container_jid, 
            is_active=True
        ).exclude(id=container_jid) # Excluir el propio contenedor

        # 2. Filtrado Semántico JSONB
        # Django soporta lookups de JSONField: metadata__key__operator
        # Convertimos el diccionario 'filters' en kwargs de Django
        # Ejemplo: filters={'gravedad__gte': 1.0} -> metadata__gravedad__gte=1.0
        
        json_filters = {}
        for key, value in filters.items():
            # Asumimos que las keys en 'filters' ya vienen con el operador si es necesario
            # o son coincidencia exacta.
            # Ej: 'gravedad' -> metadata__gravedad
            # Ej: 'poblacion__gte' -> metadata__poblacion__gte
            
            # Map clean key to metadata path
            meta_path = f"metadata__{key}"
            json_filters[meta_path] = value

        if json_filters:
            query = query.filter(**json_filters)

        # 3. Optimización Select
        # Solo traemos campos necesarios
        results = query.values('id', 'public_id', 'name', 'metadata', 'id_lore')
        
        return list(results)
