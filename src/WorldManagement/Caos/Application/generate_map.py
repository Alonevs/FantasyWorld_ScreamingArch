import base64
import os
import re
import random
from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import ImageGenerator
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service 


class GenerateWorldMapUseCase:
    """
    Caso de Uso responsable de la generación de arte conceptual e imágenes de los mundos.
    Utiliza un flujo de dos pasos:
    1. Traducción y Optimización del Prompt: Convierte la descripción en español del
       mundo a un prompt técnico en inglés optimizado para Stable Diffusion mediante Llama.
    2. Generación artística: Invoca a la IA de imagen para crear el visual.
    """
    def __init__(self, repository: CaosRepository, image_service: ImageGenerator):
        self.repository = repository
        self.image_service = image_service
        self.base_folder = os.path.abspath("src/Infrastructure/DjangoFramework/persistence/static/persistence/img")
        self.translator = Llama3Service() 

    def _sanitize(self, name):
        """Limpia nombres de archivos para evitar problemas en el sistema de ficheros."""
        s = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
        return re.sub(r'_+', '_', s)

    def _get_translated_prompt(self, world):
        """
        Traduce el lore del mundo al inglés y lo enriquece con etiquetas de calidad.
        Utiliza el motor de Llama para asegurar coherencia narrativa en la imagen.
        """
        desc_es = world.lore_description
        if not desc_es: 
            desc_es = f"Un lugar de fantasía llamado {world.name}"
        
        try:
            # Solicitar a la IA una versión técnica y artística en inglés del lore
            prompt_en = self.translator.generate_sd_prompt(world.name, desc_es)
            if prompt_en and len(prompt_en) > 5:
                print(f" ✨ Prompt optimizado: {prompt_en[:60]}...")
                return prompt_en
        except Exception as e:
            print(f" ⚠️ Fallo en la traducción del prompt ({e}). Usando configuración de seguridad.")
        
        # Fallback determinista en caso de error del servicio de traducción
        return f"{world.name}, fantasy concept art, highly detailed, masterpiece"

    def generate_preview(self, world_id_str: str):
        """
        Genera una vista previa de la imagen y la devuelve en formato Base64.
        No persiste la imagen en el servidor, solo la muestra al usuario para validación.
        """
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        if not world: 
            return None

        # Obtener el prompt optimizado y añadir variaciones estilísticas aleatorias
        final_prompt = self._get_translated_prompt(world)
        estilos = ["iluminación cinemática", "niebla atmosférica", "sombras dramáticas", "hora dorada"]
        # Nota: Los estilos se añaden en inglés para Stable Diffusion
        estilos_en = ["cinematic lighting", "atmospheric fog", "dramatic shadows", "golden hour"]
        final_prompt = f"{final_prompt}, {random.choice(estilos_en)}"
        
        print(f" 🎨 Invocando motor de imagen para '{world.name}'...")
        return self.image_service.generate_concept_art(final_prompt)

    def execute_single(self, world_id_str: str):
        """
        Genera y guarda físicamente la imagen en la base de datos de persistencia.
        """
        img_base64 = self.generate_preview(world_id_str)
        if img_base64:
            self.repository.save_image(world_id_str, img_base64)
            return True
        return None