from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Shared.Domain import eclai_core

class CreateWorldUseCase:
    """
    Caso de Uso: Crear un Nuevo Mundo (Nivel Caos).
    
    Orquesta la creación de una nueva entidad raíz en el universo.
    Responsabilidades:
    1. Generar el ID Jerárquico (J-ID) para el nuevo mundo.
    2. Generar el ID Narrativo (N-ID) para su Lore inicial.
    3. Persistir la entidad a través del repositorio.
    """
    
    def __init__(self, repository: CaosRepository):
        """
        Args:
            repository (CaosRepository): Implementación concreta del repositorio para persistencia.
        """
        self.repository = repository

    def execute(self, name: str, description: str) -> str:
        """
        Ejecuta la lógica de creación del mundo.

        Args:
            name (str): Nombre del mundo.
            description (str): Descripción narrativa inicial (Lore).

        Returns:
            str: El J-ID del mundo creado (ej. "01").
        """
        # --- PASO 1: GENERACIÓN DEL J-ID (ENTIDAD) ---
        # Nivel 1 (Caos) -> "01"
        jid_entidad = "01"
        
        # --- CORRECCIÓN CLAVE ---
        # Usamos encode_eclai126 DIRECTAMENTE.
        # Al ser "01" (2 dígitos), el sistema ya sabe implícitamente que es Nivel 1.
        # No usamos nid_to_encoded() para evitar que le añada el prefijo "01" extra.
        codigo_entidad = eclai_core.encode_eclai126(jid_entidad)

        # --- PASO 2: LORE (Aquí sí usamos N-ID completo) ---
        nid_lore = eclai_core.generar_nid(jid_entidad, "L", 1)
        # Para el Lore (01L01) sí podemos usar la codificación estándar o la directa,
        # usaremos la directa también para consistencia visual.
        codigo_lore = eclai_core.encode_eclai126(nid_lore)

        # --- PASO 3: PERSISTENCIA ---
from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Shared.Domain import eclai_core

class CreateWorldUseCase:
    """
    Caso de Uso: Crear un Nuevo Mundo (Nivel Caos).
    
    Orquesta la creación de una nueva entidad raíz en el universo.
    Responsabilidades:
    1. Generar el ID Jerárquico (J-ID) para el nuevo mundo.
    2. Generar el ID Narrativo (N-ID) para su Lore inicial.
    3. Persistir la entidad a través del repositorio.
    """
    
    def __init__(self, repository: CaosRepository):
        """
        Args:
            repository (CaosRepository): Implementación concreta del repositorio para persistencia.
        """
        self.repository = repository

    def execute(self, name: str, description: str) -> str:
        """
        Ejecuta la lógica de creación del mundo.

        Args:
            name (str): Nombre del mundo.
            description (str): Descripción narrativa inicial (Lore).

        Returns:
            str: El J-ID del mundo creado (ej. "01").
        """
        # --- PASO 1: GENERACIÓN DEL J-ID (ENTIDAD) ---
        # Nivel 1 (Caos) -> "01"
        jid_entidad = "01"
        
        # --- CORRECCIÓN CLAVE ---
        # Usamos encode_eclai126 DIRECTAMENTE.
        # Al ser "01" (2 dígitos), el sistema ya sabe implícitamente que es Nivel 1.
        # No usamos nid_to_encoded() para evitar que le añada el prefijo "01" extra.
        codigo_entidad = eclai_core.encode_eclai126(jid_entidad)

        # --- PASO 2: LORE (Aquí sí usamos N-ID completo) ---
        nid_lore = eclai_core.generar_nid(jid_entidad, "L", 1)
        # Para el Lore (01L01) sí podemos usar la codificación estándar o la directa,
        # usaremos la directa también para consistencia visual.
        codigo_lore = eclai_core.encode_eclai126(nid_lore)

        # --- PASO 3: PERSISTENCIA ---
        new_world = CaosWorld(
            id=WorldID(jid_entidad), 
            name=name, 
            lore_description=description
        )
        
        self.repository.save(new_world)
        
        # --- PROPOSAL CREATION (ECLAI v5.0) ---
        from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
        try:
            w_orm = CaosWorldORM.objects.get(id=jid_entidad)
            CaosVersionORM.objects.create(
                world=w_orm,
                proposed_name=name,
                proposed_description=description,
                version_number=1,
                status='PENDING',
                change_log="Creación inicial (Root)",
                author=None
            )
        except Exception as e: print(f"Error creating proposal: {e}")
        
        print(f" ✅ [ECLAI v3.0] Mundo 'Caos' (Nivel 1) creado.")
        print(f" ---------------------------------------------------")
        print(f" 🏛️  TABLA ENTIDADES (Mundos):")
        print(f"    └── J-ID: {jid_entidad}")
        print(f"    └── CODE: {codigo_entidad}   <-- ¡Código Corto Puro!")
        print(f"")
        print(f" 📜 TABLA NARRATIVA (Lore):")
        print(f"    └── N-ID: {nid_lore}")
        print(f"    └── CODE: {codigo_lore}")
        print(f" ---------------------------------------------------")
        
        return jid_entidad