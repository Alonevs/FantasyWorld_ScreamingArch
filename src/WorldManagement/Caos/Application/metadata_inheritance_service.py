from ..Domain.metadata import INHERITANCE_RULES
from ..Domain.repositories import CaosRepository

class MetadataInheritanceService:
    def __init__(self, repository: CaosRepository):
        self.repo = repository

    def get_consolidated_metadata(self, entity):
        local_data = entity.metadata.get('datos_nucleo', {})
        inherited_data = {}
        
        # Obtener ancestros (Padre, Abuelo, etc.)
        ancestors = self.repo.get_ancestors_by_id(entity.j_id) # Debe estar ordenado de Lejano a Cercano

        for ancestor in ancestors:
            anc_meta = ancestor.metadata.get('datos_nucleo', {})
            # Buscar coincidencia con reglas
            for key, rule in INHERITANCE_RULES.items():
                if key in anc_meta:
                    # Sobrescribir herencia previa (el ancestro más cercano gana)
                    # Pero NO sobrescribir dato local si ya existe
                    if key not in local_data:
                        inherited_data[key] = {
                            "value": anc_meta[key],
                            "source": ancestor.name,
                            "is_inherited": True
                        }
        
        return { "local": local_data, "inherited": inherited_data }
