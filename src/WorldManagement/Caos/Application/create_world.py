from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository

class CreateWorldUseCase:
    """
    Caso de Uso: Crear un Nuevo Mundo (Nivel Caos).
    
    Orquesta la creación de una nueva entidad raíz en el universo.
    Responsabilidades:
    1. Generar el ID Jerárquico (J-ID) para el nuevo mundo.
    2. Persistir la entidad a través del repositorio.
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
        print(f"    └── J-ID: {jid_entidad}")
        
        return jid_entidad