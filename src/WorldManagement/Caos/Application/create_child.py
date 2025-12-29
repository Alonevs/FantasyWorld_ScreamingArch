from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository

class CreateChildWorldUseCase:
    """
    Caso de Uso responsable de la creación de una entidad hija dentro de la jerarquía.
    Maneja la lógica de asignación de J-ID (incluyendo saltos de nivel), generación opcional
    de imágenes y texto mediante IA, y la creación automática de la propuesta inicial.
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, parent_id: str, name: str, description: str, reason: str = "Creación inicial", generate_image: bool = False, target_level: int = None, user=None) -> str:
        print(f" 🐣 Iniciando nacimiento de una nueva entidad en {parent_id} (Nivel Objetivo: {target_level})...")

        # 1. Calcular el J-ID del nuevo hijo
        # Delegamos en el repositorio para manejar el relleno (padding '00') si se trata de un salto jerárquico.
        new_child_id = self.repository.get_next_child_id(parent_id, target_level=target_level)
        
        print(f"    J-ID Calculado: {new_child_id}")

        # --- LÓGICA DE FANTASMAS ELIMINADA ---
        # No se crean entidades físicas intermedio para rellenar huecos.
        # La capa visual se encarga de "izar" a los hijos si no hay niveles intermedios poblados.

        # --- GENERACIÓN DE TEXTO POR IA (Opcional) ---
        if generate_image: # Reutilizamos el flag de imagen como indicador general de ayuda por IA
            try:
                print(f"    🧠 [Llama] Expandiendo descripción para {name}...")
                from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
                llama = Llama3Service()
                expanded_desc = llama.generate_description(f"{name}. {description}")
                if expanded_desc:
                    description = expanded_desc
                    print(f"    ✅ Descripción expandida por IA.")
            except Exception as e:
                print(f"    ⚠️ Error en Llama 3: {e}")

        # 2. Instanciar la Entidad de Dominio
        # Por defecto, todas las creaciones nuevas nacen con estatus 'DRAFT' (Borrador).
        new_world = CaosWorld(
            id=WorldID(new_child_id), 
            name=name, 
            lore_description=description,
            status='DRAFT'
        )
        
        # 3. Persistir en el repositorio
        self.repository.save(new_world)
        
        # --- CREACIÓN DE PROPUESTA INICIAL (Ciclo de Vida de Versiones) ---
        from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosImageProposalORM
        
        try:
            # Recuperamos el objeto ORM recién creado
            w_orm = CaosWorldORM.objects.get(id=new_child_id)
            
            # Generamos la Versión 1 como PENDIENTE de aprobación
            CaosVersionORM.objects.create(
                world=w_orm,
                proposed_name=name,
                proposed_description=description,
                version_number=1,
                status='PENDING',
                change_log=reason,
                author=user  # Vinculado al usuario que ejecuta el comando
            )
            print(f"    📝 Propuesta v1 (PENDIENTE) creada para {name}")
            
            # --- GENERACIÓN DE IMAGEN POR IA (Opcional) ---
            if generate_image:
                print(f"    🎨 Generando imagen conceptual inicial para {name}...")
                try:
                    from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
                    from django.core.files.base import ContentFile
                    import base64
                    import io
                    from PIL import Image
                    
                    sd = StableDiffusionService()
                    # Creamos un prompt basado en el nombre y la descripción expandida
                    prompt = f"{name}, {description[:200]}, fantasy concept art, detailed, masterpiece"
                    b64_img = sd.generate_concept_art(prompt)
                    
                    if b64_img:
                        # Decodificación y conversión a formato WebP para optimizar peso/calidad
                        image = Image.open(io.BytesIO(base64.b64decode(b64_img)))
                        output = io.BytesIO()
                        image.save(output, format='WEBP')
                        
                        nombre_fichero = f"{name.replace(' ', '_')}_v1.webp"
                        image_data = ContentFile(output.getvalue(), name=nombre_fichero)
                        
                        # Las imágenes también nacen como propuestas PENDIENTES
                        CaosImageProposalORM.objects.create(
                            world=w_orm,
                            image=image_data,
                            title=f"Arte Inicial: {name}",
                            author=user,  # Vinculado al usuario que ejecuta el comando
                            status='PENDING'
                        )
                        print(f"    ✅ Propuesta de imagen creada: {nombre_fichero}")
                    else:
                        print("    ⚠️ La IA no devolvió ninguna imagen.")
                except Exception as e:
                    print(f"    ⚠️ Error en generación de imagen (SD): {e}")

        except Exception as e:
            print(f"    ❌ Error crítico en procesos post-creación: {e}")
            import traceback
            traceback.print_exc()

        # Resumen final en log
        print(f" ✨ [ECLAI] Entidad hija creada con éxito: {name}")
        print(f"    └── J-ID: {new_child_id}")
        
        return new_child_id