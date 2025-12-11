import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.WorldManagement.Caos.Domain.metadata import METADATA_SCHEMAS, INHERITANCE_RULES
from src.WorldManagement.Caos.Domain.metadata_router import get_schema_for_hierarchy
from src.WorldManagement.Caos.Application.metadata_inheritance_service import MetadataInheritanceService

def test_metadata_schemas():
    print("\n--- Testing Metadata Schemas ---")
    expected_schemas = [
        "CAOS_SCHEMA", "ABISMO_SCHEMA", "UNIVERSO_SCHEMA", "GALAXIA_SCHEMA",
        "SISTEMA_SCHEMA", "PLANETA_SCHEMA", "DIMENSION_SCHEMA",
        "GEOGRAFIA_SCHEMA", "SOCIEDAD_SCHEMA", "CRIATURA_SCHEMA", "OBJETO_SCHEMA"
    ]
    for schema in expected_schemas:
        if schema in METADATA_SCHEMAS:
            print(f"✅ Schema {schema} exists.")
        else:
            print(f"❌ Schema {schema} MISSING!")

def test_metadata_router():
    print("\n--- Testing Metadata Router ---")
    
    # Test Level 1 (Caos)
    schema = get_schema_for_hierarchy("CAOS-0000", 1)
    print(f"Level 1 Schema: {schema == METADATA_SCHEMAS['CAOS_SCHEMA']} (Expected: CAOS_SCHEMA)")
    
    # Test Level 6 (Planeta vs Dimension)
    # 0101... -> Planet
    schema_planet = get_schema_for_hierarchy("0101-REST", 6)
    print(f"Level 6 Planet Schema: {schema_planet == METADATA_SCHEMAS['PLANETA_SCHEMA']} (Expected: PLANETA_SCHEMA)")
    
    # Other -> Dimension
    schema_dim = get_schema_for_hierarchy("0102-REST", 6)
    print(f"Level 6 Dimension Schema: {schema_dim == METADATA_SCHEMAS['DIMENSION_SCHEMA']} (Expected: DIMENSION_SCHEMA)")

    # Test Level 16 (Criatura vs Objeto)
    # JID index 24:26. 
    # Example JID len must be enough.
    # 012345678901234567890123456789 (30 chars)
    # "000000000000000000000000950000" -> index 24 starts at '9'
    # Let's construct a dummy JID with correct length or just enough for slicing.
    # get_schema_for_hierarchy uses `jid[24:26]`
    
    # Case: Objeto (90+)
    jid_obj = "X" * 24 + "95" + "X" * 10
    schema_obj = get_schema_for_hierarchy(jid_obj, 16)
    print(f"Level 16 Objeto Schema: {schema_obj == METADATA_SCHEMAS['OBJETO_SCHEMA']} (Expected: OBJETO_SCHEMA)")
    
    # Case: Criatura (50)
    jid_creature = "X" * 24 + "50" + "X" * 10
    schema_creature = get_schema_for_hierarchy(jid_creature, 16)
    print(f"Level 16 Criatura Schema: {schema_creature == METADATA_SCHEMAS['CRIATURA_SCHEMA']} (Expected: CRIATURA_SCHEMA)")
    
def test_inheritance_service():
    print("\n--- Testing Inheritance Service ---")
    
    # Mock Entities
    class MockEntity:
        def __init__(self, j_id, name, metadata):
            self.j_id = j_id
            self.name = name
            self.metadata = metadata

    # Setup Hierarchy
    # Planeta (Root for physics) -> ... -> Ciudad (Geo/Soc) -> Criatura
    
    planeta = MockEntity("PLANETA_ID", "Tierra", {
        "datos_nucleo": {
            "gravedad": "1.0g",
            "atmosfera": "Respirable"
        }
    })
    
    ciudad = MockEntity("CIUDAD_ID", "Ventormenta", {
        "datos_nucleo": {
            "bioma_dominante": "Bosque",
            "idioma_oficial": "Común", # Inherited from society, theoretically, but defined here for propagation test
            "nivel_tecnologico": "Medieval"
        }
    })
    
    criatura = MockEntity("CRIATURA_ID", "Lobo", {
        "datos_nucleo": {
            "nombre_raza": "Lobo",
            # Should inherit gravity, atmosfera, bioma, idioma
            # Local override: None
        }
    })

    # Mock Repository
    mock_repo = MagicMock()
    # Return ancestors for criatura: [Planeta, Ciudad] (Furthest to Closest)
    mock_repo.get_ancestors_by_id.return_value = [planeta, ciudad]
    
    service = MetadataInheritanceService(mock_repo)
    
    result = service.get_consolidated_metadata(criatura)
    
    inherited = result['inherited']
    print(f"Consolidated Keys: {list(inherited.keys())}")
    
    # Checks
    print(f"Inherited Gravity: {inherited.get('gravedad', {}).get('value')} (Expected: 1.0g)")
    print(f"Inherited Bioma: {inherited.get('bioma_dominante', {}).get('value')} (Expected: Bosque)")
    print(f"Inherited Idioma: {inherited.get('idioma_oficial', {}).get('value')} (Expected: Común)")
    print(f"Inherited Source Gravity: {inherited.get('gravedad', {}).get('source')} (Expected: Tierra)")

if __name__ == "__main__":
    test_metadata_schemas()
    test_metadata_router()
    test_inheritance_service()
