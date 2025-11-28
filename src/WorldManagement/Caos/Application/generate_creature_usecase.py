from src.WorldManagement.Caos.Domain.creature import Creature
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator, ImageGenerator

class GenerateCreatureUseCase:
    """
    Orquesta la creación de una criatura usando IA Textual (Biología) y Visual (Foto).
    """
    def __init__(self, repository: CaosRepository, lore_service: LoreGenerator, image_service: ImageGenerator):
        self.repo = repository
        self.llama = lore_service
        self.sd = image_service

    def execute(self, parent_id: str) -> str:
        # 1. Obtener contexto del padre (Planeta/Región)
        # Nota: find_by_id acepta string o WorldID gracias al repo inteligente
        parent = self.repo.find_by_id(parent_id)
        if not parent:
            raise Exception(f"Padre {parent_id} no encontrado")

        print(f" 🧬 Diseñando forma de vida para: {parent.name}...")

        # 2. Generar Biología (Llama 3)
        system_prompt = """
        Role: Expert Xenobiologist.
        Task: Design a unique fauna species for the provided environment.
        Output: STRICT JSON.
        Keys required: name, taxonomy, description, danger_level (int 1-10), behavior, visual_dna (list), sd_prompt.
        """
        
        context_prompt = f"World: {parent.name}. Context: {parent.lore_description}"
        
        bio_data = self.llama.generate_structure(system_prompt, context_prompt)

        # Fallback de seguridad
        if not bio_data:
            bio_data = {
                "name": "Especie Desconocida",
                "taxonomy": "Anomalía",
                "description": "Datos biológicos corruptos o ilegibles.",
                "danger_level": 1,
                "behavior": "Errático",
                "visual_dna": ["glitch", "shadow"],
                "sd_prompt": "glitch artifact, error texture"
            }

        # 3. Calcular ID (ECLAI Nivel 16)
        # El repositorio ya sabe que las criaturas van al nivel 16
        new_id = self.repo.get_next_child_id(parent_id)

        # 4. Crear Entidad Dominio
        creature = Creature.from_ai_data(bio_data, parent_id)
        creature.eclai_id = new_id

        # 5. Generar Imagen (Stable Diffusion)
        print(f" 🎨 Renderizando espécimen: {creature.name}")
        image_base64 = self.sd.generate_concept_art(creature.sd_prompt)

        # 6. Persistencia
        self.repo.save_creature(creature)
        
        if image_base64:
            self.repo.save_image(new_id, image_base64)
            
        return new_id
