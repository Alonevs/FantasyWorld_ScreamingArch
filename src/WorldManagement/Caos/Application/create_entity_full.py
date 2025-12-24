from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService


class CreateEntityFullUseCase:
    """
    Caso de Uso avanzado para la creación "llave en mano" de una entidad compleja (ej: Criaturas).
    A diferencia de la creación simple, este proceso genera simultáneamente:
    1. El J-ID jerárquico.
    2. Una ficha técnica en formato JSON (biología, rasgos, etc.) mediante Llama.
    3. Una ilustración conceptual mediante Stable Diffusion.
    """
    def __init__(self, repository: CaosRepository):
        self.repo = repository
        self.ia_text = Llama3Service()
        self.ia_art = StableDiffusionService()

    def execute(self, parent_id: str, name: str, tipo: str):
        """
        Ejecuta el ciclo completo de creación (ID -> Texto -> Imagen -> Persistencia).
        
        Args:
            parent_id: El ID del contenedor padre.
            name: Nombre de la nueva entidad.
            tipo: Categoría taxonómica (Criatura, Objeto, etc.) para guiar a la IA.
        """
        # 1. Validación del entorno jerárquico
        parent = self.repo.find_by_id(WorldID(parent_id))
        if not parent: 
            return None
        
        # 2. Asignación del siguiente identificador disponible
        new_id = self.repo.get_next_child_id(parent_id)
        
        # 3. Generación Estructurada (JSON) por IA
        # Solicitamos a la IA que cree una descripción y rasgos biográficos/técnicos.
        print(f" 🧬 Generando ficha técnica por IA para: {name}...")
        datos = self.ia_text.generate_entity_json(name, tipo, parent.name)
        
        desc = datos.get("descripcion", f"Una entidad de tipo {tipo}.")
        rasgos = datos.get("rasgos", f"Rasgos descriptivos de {name}.")

        # 4. Generación Artística (Concept Art)
        # Se envía un prompt combinado de nombre, tipo y rasgos a Stable Diffusion.
        print(f" 🎨 Generando ilustración conceptual...")
        self.ia_art.generate_concept_art(f"{name}, {tipo}, {rasgos}", category="criatura")
        
        # 5. Constitución de la Entidad de Dominio
        # Se guarda inicialmente como BORRADOR (DRAFT) y oculta al público.
        entity = CaosWorld(
            id=WorldID(new_id),
            name=name,
            lore_description=desc,
            status="DRAFT",
            metadata=datos, # Almacenamos toda la ficha técnica generada
            visible_publico=False
        )
        
        # 6. Almacenamiento
        self.repo.save(entity)
        
        print(f" ✨ Entidad completa '{name}' creada con éxito en la jerarquía.")
        return new_id