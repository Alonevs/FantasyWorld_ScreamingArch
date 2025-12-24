from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository

class CreateWorldUseCase:
    """
    Caso de Uso responsable de la creación de una nueva Entidad Raíz (Nivel 1).
    Orquesta la asignación de un nuevo J-ID libre en la base de la jerarquía 
    y genera la primera propuesta de versión (V1) para que los administradores
    puedan revisar el alta del mundo.
    """
    
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, name: str, description: str) -> str:
        """
        Ejecuta la lógica de creación del mundo raíz.

        Args:
            name (str): Nombre del mundo.
            description (str): Descripción narrativa inicial.

        Returns:
            str: El J-ID generado (ej. "01", "02").
        """
        # --- PASO 1: GENERACIÓN DEL J-ID (Filling Gaps) ---
        # Buscamos el primer identificador de 2 caracteres que esté libre.
        from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
        from django.db.models.functions import Length
        
        # Obtenemos los IDs existentes de Nivel 1
        existing = set(CaosWorldORM.objects.annotate(ilen=Length('id')).filter(ilen=2).values_list('id', flat=True))
        
        next_val = 1
        while f"{next_val:02d}" in existing:
            next_val += 1
            
        jid_entidad = f"{next_val:02d}"
        
        # --- PASO 2: PERSISTENCIA EN EL DOMINIO ---
        new_world = CaosWorld(
            id=WorldID(jid_entidad), 
            name=name, 
            lore_description=description
        )
        
        self.repository.save(new_world)
        
        # --- PASO 3: CREACIÓN DE LA PROPUESTA (ECLAI Workflow) ---
        # Todo nuevo mundo nace como una propuesta PENDIENTE de revisión.
        from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
        try:
            w_orm = CaosWorldORM.objects.get(id=jid_entidad)
            CaosVersionORM.objects.create(
                world=w_orm,
                proposed_name=name,
                proposed_description=description,
                version_number=1,
                status='PENDING',
                change_log="Alta inicial de Entidad Raíz (Nivel 1)",
                author=None
            )
        except Exception as e: 
            print(f"Error al generar propuesta inicial: {e}")
        
        print(f" ✅ Entidad Raíz '{name}' (Nivel 1) creada.")
        print(f"    └── J-ID Asignado: {jid_entidad}")
        
        return jid_entidad