from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.Shared.Domain import eclai_core

class CreateEntityFullUseCase:
    def __init__(self, repository: CaosRepository):
        self.repo = repository
        self.ia_text = Llama3Service()
        self.ia_art = StableDiffusionService()

    def execute(self, parent_id: str, name: str, tipo: str):
        # 1. Buscar Padre
        parent = self.repo.find_by_id(WorldID(parent_id))
        if not parent: return None
        
        # 2. Calcular ID Hijo
        new_id = self.repo.get_next_child_id(parent_id)
        
        # 3. Generar Datos (JSON)
        print(f" 🧬 Generando ficha técnica para: {name}...")
        datos = self.ia_text.generate_entity_json(name, tipo, parent.name)
        
        desc = datos.get("descripcion", f"Una entidad de tipo {tipo}.")
        rasgos = datos.get("rasgos", f"A {tipo} creature")

        # 4. Generar Imagen
        print(f" 🎨 Pintando criatura...")
        # Usamos el modelo 'criatura' si está configurado en sd_service, o el defecto
        self.ia_art.generate_concept_art(f"{name}, {tipo}, {rasgos}", category="criatura")
        
        # 5. Guardar Entidad
        entity = CaosWorld(
            id=WorldID(new_id),
            name=name,
            lore_description=desc,
            status="DRAFT",
            metadata=datos, # Guardamos el JSON completo
            visible_publico=False
        )
        
        self.repo.save(entity)
        return new_id