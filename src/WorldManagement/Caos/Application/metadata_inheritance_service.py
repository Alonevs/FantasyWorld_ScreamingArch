from ..Domain.metadata import INHERITANCE_RULES
from ..Domain.repositories import CaosRepository

class MetadataInheritanceService:
    """
    Servicio responsable de calcular la herencia de propiedades entre niveles jerárquicos.
    Permite que un planeta herede el clima de su sistema solar, o que un personaje 
    herede las leyes mágicas de su universo, permitiendo sobrescrituras locales.
    """
    def __init__(self, repository: CaosRepository):
        self.repo = repository

    def get_consolidated_metadata(self, entity):
        """
        Calcula el estado final de los metadatos de una entidad, combinando sus datos
        propios con los heredados de sus ancestros.
        
        Lógica: El ancestro más cercano (Padre) tiene prioridad sobre el más lejano (Abuelo),
        pero el dato local siempre es la "verdad absoluta".
        """
        local_data = entity.metadata.get('datos_nucleo', {})
        inherited_data = {}
        
        # Recuperar ancestros ordenados de Lejano (Raíz) a Cercano (Padre)
        ancestors = self.repo.get_ancestors_by_id(entity.j_id)

        for ancestor in ancestors:
            anc_meta = ancestor.metadata.get('datos_nucleo', {})
            
            # Aplicar reglas de herencia definidas en el dominio
            for key, rule in INHERITANCE_RULES.items():
                if key in anc_meta:
                    # El ancestro más cercano en el bucle sobrescribirá los valores de ancestros previos.
                    # Solo lo añadimos a heredados si la entidad actual NO tiene un valor local propio.
                    if key not in local_data:
                        inherited_data[key] = {
                            "value": anc_meta[key],
                            "source": ancestor.name,
                            "is_inherited": True
                        }
        
        return { "local": local_data, "inherited": inherited_data }
