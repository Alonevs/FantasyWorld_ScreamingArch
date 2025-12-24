from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase

class DeepCreationService:
    """
    Servicio especializado en la creación de jerarquías de "Salto Profundo".
    Permite crear una entidad en un nivel muy distante (ej: nivel 13) desde un padre
    en un nivel superior (ej: nivel 3), rellenando automáticamente los niveles 
    intermedios con contenedores estructurales (GAPs) para mantener la integridad del J-ID.
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository
        self.child_creator = CreateChildWorldUseCase(repository)

    def create_descendant_at_level(self, parent_id: str, target_level: int, name: str, description: str, reason: str, generate_image: bool = False) -> str:
        """
        Crea una entidad descendiente en el nivel objetivo, generando puentes estructurales.
        
        Args:
            parent_id: El ID del ancestro actual.
            target_level: El nivel de destino (numérico) donde debe nacer la entidad.
            name: Nombre de la entidad final.
            description: Lore de la entidad final.
            reason: Motivo del cambio (para el historial de versiones).
        """
        current_jid = parent_id
        current_level = len(current_jid) // 2
        
        print(f"🚀 [DeepCreation] Iniciando Salto Profundo Jerárquico: Nivel {current_level} -> {target_level}")
        
        # 1. Bucle de generación de puentes intermedios (GAPs)
        # Rellenamos los niveles desde el actual + 1 hasta el objetivo - 1.
        for lvl in range(current_level + 1, target_level):
            # Estandarizamos el ID del puente usando el sufijo de salto '00'
            gap_id = current_jid + "00"
            
            # Verificamos si el puente ya existe para reutilizarlo
            gap = self.repository.find_by_id(WorldID(gap_id))
            if not gap:
                print(f"  👻 Generando Puente Estructural (GAP) en Nivel {lvl}: {gap_id}")
                gap_world = CaosWorld(
                    id=WorldID(gap_id),
                    name="_CONTENEDOR_ESTRUCTURAL_",
                    lore_description="Estructura jerárquica para habilitar niveles profundos.",
                    status='LIVE', # Los puentes nacen activos para permitir la navegación
                    metadata={"tipo": "GAP_ESTRUCTURAL"}
                )
                self.repository.save(gap_world)
            else:
                print(f"  👻 Reutilizando puente existente en Nivel {lvl}: {gap_id}")
            
            # Actualizamos el puntero para el siguiente nivel del bucle
            current_jid = gap_id
            
        # 2. Creación de la Entidad Final en el nivel objetivo
        # Una vez construida la "escalera" de puentes, creamos la entidad real bajo el último GAP.
        print(f"  ✨ Meta alcanzada. Creando entidad definitiva '{name}' bajo el padre {current_jid}...")
        
        # Reutilizamos el Caso de Uso estándar para asegurar que se cree con su propuesta de versión (V1).
        final_id = self.child_creator.execute(current_jid, name, description, reason, generate_image)
        return final_id
