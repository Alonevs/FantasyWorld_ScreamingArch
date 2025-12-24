from src.WorldManagement.Caos.Domain.creature import Creature
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator, ImageGenerator

class GenerateCreatureUseCase:
    """
    Orquesta la creación de una nueva especie de fauna (Criaturas) utilizando IA.
    Este proceso combina la generación de biología evolutiva (Llama) con la 
    renderización visual (Stable Diffusion) para crear seres coherentes con su entorno.
    """
    def __init__(self, repository: CaosRepository, lore_service: LoreGenerator, image_service: ImageGenerator):
        self.repo = repository
        self.llama = lore_service
        self.sd = image_service

    def execute(self, parent_id: str) -> str:
        """
        Diseña una criatura adaptada al medio ambiente de su contenedor padre.
        
        Args:
            parent_id: El ID de la entidad donde habita la criatura (ej: un continente o planeta).
        """
        # 1. Análisis del Ecosistema (Contexto del Padre)
        parent = self.repo.find_by_id(parent_id)
        if not parent:
            raise Exception(f"No se ha encontrado el entorno padre: {parent_id}")

        print(f" 🧬 Diseñando forma de vida adaptada a: {parent.name}...")

        # 2. Generación de Biología Evolutiva (IA Textual)
        system_prompt = """
        Rol: Xenobiólogo Experto.
        Tarea: Diseñar una especie de fauna única adaptada al entorno proporcionado.
        Salida: JSON ESTRICTO.
        Claves: name, taxonomy, description, danger_level (1-10), behavior, visual_dna (lista), sd_prompt.
        """
        
        context_prompt = f"Entorno: {parent.name}. Lore del clima/entorno: {parent.lore_description}"
        
        # Invocación generadora de estructura
        bio_data = self.llama.generate_structure(system_prompt, context_prompt)

        # Mecanismo de seguridad (Fallback) por si falla la IA
        if not bio_data:
            bio_data = {
                "name": "Especie Desconocida",
                "taxonomy": "Anomalía Biológica",
                "description": "Datos de ADN corruptos.",
                "danger_level": 0,
                "behavior": "Pasivo",
                "visual_dna": ["indeterminado"],
                "sd_prompt": "foggy creature silhouette"
            }

        # 3. Asignación Jerárquica
        # Las criaturas suelen pertenecer a niveles profundos de la jerarquía (Nivel 16).
        new_id = self.repo.get_next_child_id(parent_id)

        # 4. Construcción de la Entidad de Dominio
        # Utilizamos el factory method de la entidad Creature para mapear el JSON.
        creature = Creature.from_ai_data(bio_data, parent_id)
        creature.eclai_id = new_id

        # 5. Renderización Visual (IA de Imagen)
        print(f" 🎨 Generando visual del espécimen: {creature.name}")
        image_base64 = self.sd.generate_concept_art(creature.sd_prompt)

        # 6. Almacenamiento y Persistencia
        self.repo.save_creature(creature)
        
        if image_base64:
            self.repo.save_image(new_id, image_base64)
            
        return new_id
