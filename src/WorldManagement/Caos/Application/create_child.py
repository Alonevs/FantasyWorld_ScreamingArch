from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Shared.Domain import eclai_core

class CreateChildWorldUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, parent_id: str, name: str, description: str, reason: str = "Creación inicial", generate_image: bool = False, target_level: int = None) -> str:
        print(f" 🐣 Iniciando nacimiento de una nueva entidad en {parent_id} (Target Level: {target_level})...")

        # 1. Calcular el ID del nuevo hijo
        # Delegamos completamente en el repositorio para manejar relleno (padding) si es un salto
        new_child_id = self.repository.get_next_child_id(parent_id, target_level=target_level)
        
        print(f"    Calculado ID: {new_child_id}")

        # --- AI TEXT GENERATION (Optional) ---
        if generate_image: # Reusing the flag as "use_ai"
            try:
                print(f"    🧠 [Llama] Expandiendo descripción para {name}...")
                from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
                llama = Llama3Service()
                expanded_desc = llama.generate_description(f"{name}. {description}")
                if expanded_desc:
                    description = expanded_desc
                    print(f"    ✅ Descripción expandida: {description[:50]}...")
            except Exception as e:
                print(f"    ⚠️ Falló Llama 3: {e}")

        # 2. Crear la Entidad
        new_world = CaosWorld(
            id=WorldID(new_child_id), 
            name=name, 
            lore_description=description,
            status='DRAFT' # Explicitly set to DRAFT
        )
        
        # 3. Guardar
        self.repository.save(new_world)
        
        # --- PROPOSAL CREATION (ECLAI v5.0) ---
        from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosImageProposalORM
        
        try:
            w_orm = CaosWorldORM.objects.get(id=new_child_id)
            
            CaosVersionORM.objects.create(
                world=w_orm,
                proposed_name=name,
                proposed_description=description,
                version_number=1,
                status='PENDING',
                change_log=reason,
                author=None 
            )
            print(f"    📝 Propuesta v1 creada para {name}")
            
            # --- IMAGE GENERATION (Optional) ---
            if generate_image:
                print(f"    🎨 Generando imagen inicial para {name}...")
                from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
                from django.core.files.base import ContentFile
                import base64
                import io
                from PIL import Image
                
                sd = StableDiffusionService()
                # Use the expanded description for better prompts if available
                prompt = f"{name}, {description[:200]}, fantasy concept art, detailed, masterpiece"
                b64_img = sd.generate_concept_art(prompt)
                
                if b64_img:
                    # Decode and convert to WebP
                    image = Image.open(io.BytesIO(base64.b64decode(b64_img)))
                    output = io.BytesIO()
                    image.save(output, format='WEBP')
                    
                    file_name = f"{name.replace(' ', '_')}_v1.webp"
                    image_data = ContentFile(output.getvalue(), name=file_name)
                    
                    # Auto-approve logic for initial creation
                    status = 'PENDING'
                    # Auto-approve logic DISABLED for Strict Approval Flow
                    status = 'PENDING'
                    # (Code removed: save_manual_file)

                    CaosImageProposalORM.objects.create(
                        world=w_orm,
                        image=image_data,
                        title=f"Arte Inicial: {name}",
                        author=None,
                        status=status
                    )
                    print(f"    ✅ Propuesta de imagen creada: {file_name} ({status})")
                else:
                    print("    ⚠️ Falló la generación de imagen.")

        except Exception as e:
            print(f"    ❌ Error en procesos post-creación: {e}")
            import traceback
            traceback.print_exc()

        # Codificación para mostrar en log
        code = eclai_core.encode_eclai126(new_child_id)
        print(f" ✨ [ECLAI] Sub-Mundo creado: {name}")
        print(f"    └── J-ID: {new_child_id} | CODE: {code}")
        
        return new_child_id