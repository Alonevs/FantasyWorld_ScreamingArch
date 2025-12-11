import os
import sys
from unittest.mock import MagicMock

# Setup Path
# We need PROJECT_ROOT (parent of src)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.WorldManagement.Caos.Domain.metadata import TYPE_MAPPING, get_schema_for_type
from src.WorldManagement.Caos.Application.generate_contextual_metadata import GenerateContextualMetadataUseCase

def test_schema_retrieval():
    print("--- TEST 1: Schema Retrieval ---")
    planet_schema = get_schema_for_type("PLANETA")
    if planet_schema and "gravedad" in planet_schema['campos_fijos']:
        print("✅ PLANETA schema looks good (Key: gravedad).")
    else:
        print(f"❌ PLANETA schema missing or invalid keys: {planet_schema and planet_schema.get('campos_fijos')}")
        
    # V2 removed get_group_for_type, so we skip that test or test TYPE_MAPPING directly
    if TYPE_MAPPING.get("CAOS_PRIME") == "CAOS_SCHEMA":
        print("✅ CAOS_PRIME maps to CAOS_SCHEMA.")
    else:
        print(f"❌ CAOS_PRIME mapping failed: {TYPE_MAPPING.get('CAOS_PRIME')}")

def test_use_case_logic():
    print("\n--- TEST 2: Use Case Mock Execution ---")
    
    # Mock dependencies
    mock_repo = MagicMock()
    mock_ai = MagicMock()
    
    # Mock World
    mock_world = MagicMock()
    mock_world.name = "Test World"
    mock_world.lore_description = "Un planeta lleno de océanos y tormentas."
    mock_world.metadata = {} # Empty initially
    
    mock_repo.find_by_id.return_value = mock_world
    
    # Case A: Infer Type
    mock_ai.edit_text.return_value = "PLANETA" # AI says it's a planet
    mock_ai.generate_structure.return_value = {"key": "value"} # Metadata result
    
    use_case = GenerateContextualMetadataUseCase(mock_repo, mock_ai)
    
    # Run
    result = use_case.execute("dummy_id")
    
    # Case B: Cold Start (Known type, No Lore)
    mock_world_cold = MagicMock()
    mock_world_cold.name = "Empty Planet"
    mock_world_cold.lore_description = "" # Empty
    mock_world_cold.description = ""
    mock_world_cold.metadata = {'tipo_entidad': 'PLANETA'} # Pre-known type
    
    mock_repo.find_by_id.return_value = mock_world_cold
    
    result_cold = use_case.execute("dummy_cold_id")
    
    # Assertions for Cold Start
    mock_ai.reset_mock()
    
    # 2. Metadata should be initialized with schema keys -> CHECK RESULT, NOT WORLD
    if result_cold and "gravedad" in result_cold['datos_nucleo']:
        print("✅ Cold Start: Initialized 'gravedad' key in RESULT.")
    else:
        print(f"❌ Cold Start failed. Result: {result_cold}")
        
    if result_cold and result_cold['datos_nucleo']['gravedad'] == "Pendiente":
        print("✅ Cold Start: Value set to 'Pendiente'.")
    else:
         print(f"❌ Cold Start value mismatch: {result_cold}")

    # Case C: Hierarchy Logic (J-ID Level)
    # ID Length 12 -> Level 6 (Planeta) -> PLANETA_SCHEMA
    mock_world_hierarchy = MagicMock()
    mock_world_hierarchy.name = "Planet By ID"
    mock_world_hierarchy.metadata = {}
    
    mock_repo.find_by_id.return_value = mock_world_hierarchy
    
    # 12-char ID
    use_case = GenerateContextualMetadataUseCase(mock_repo, mock_ai)
    # 0101...01 (12 chars)
    result_hierarchy = use_case.execute("010101010101") 
    
    # Assertions
    # Should detect Level 6, map to PLANETA_SCHEMA -> keys like gravedad
    if result_hierarchy and "gravedad" in result_hierarchy.get('datos_nucleo', {}):
        print("✅ Hierarchy Test: Correctly mapped Level 6 to PLANETA_SCHEMA (gravedad).")
    else:
        print(f"❌ Hierarchy Test Failed. Result: {result_hierarchy}")

    # Case E: Cosmology Schemas (Level 3 - Universe)
    # ID: 010101 (Level 3) -> Should be UNIVERSO_SCHEMA
    mock_world_uni = MagicMock()
    mock_world_uni.name = "Test Universe"
    mock_world_uni.metadata = {}
    mock_repo.find_by_id.return_value = mock_world_uni
    
    result_uni = use_case.execute("010101")
    
    # Check for 'leyes_fisicas_activas' (V2 key)
    if result_uni and "leyes_fisicas_activas" in result_uni.get('datos_nucleo', {}):
        print("✅ Cosmology Test: Correctly mapped Level 3 to UNIVERSO_SCHEMA (leyes_fisicas_activas).")
    else:
        print(f"❌ Cosmology Test Failed. Result: {result_uni}")

    # Case F: Cosmology Schemas (Level 4 - Galaxy)
    # ID: 01010101 (Level 4) -> Should be GALAXIA_SCHEMA
    mock_world_gal = MagicMock()
    mock_world_gal.name = "Test Galaxy"
    mock_world_gal.metadata = {}
    mock_repo.find_by_id.return_value = mock_world_gal
    
    result_gal = use_case.execute("01010101")
    
    # V2 Key: tipo_morfologia
    if result_gal and "tipo_morfologia" in result_gal.get('datos_nucleo', {}):
        print("✅ Cosmology Test: Correctly mapped Level 4 to GALAXIA_SCHEMA (tipo_morfologia).")
    else:
        print(f"❌ Cosmology Test Failed. Result: {result_gal}")

def debug_live():
    print("\n--- LIVE DB DEBUG (Auto-Noos) ---")
    try:
        import django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.Infrastructure.DjangoFramework.settings")
        # Ensure setup only if not configured
        if not django.apps.apps.ready:
            django.setup()
            
        from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
        from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
        from src.WorldManagement.Caos.Application.generate_contextual_metadata import GenerateContextualMetadataUseCase
        from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

        world = CaosWorldORM.objects.first()
        if not world:
            print("❌ No worlds found in DB.")
            return

        print(f"Target World: {world.name} (ID: {world.id})")
        repo = DjangoCaosRepository()
        ai = Llama3Service()
        use_case = GenerateContextualMetadataUseCase(repo, ai)
        
        result = use_case.execute(world.id)
        if result:
            print("✅ LIVE RESULT:")
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("❌ LIVE RESULT EMPTY.")
            
    except Exception as e:
        print(f"❌ Live Debug Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_schema_retrieval()
    test_use_case_logic()
    # debug_live()
