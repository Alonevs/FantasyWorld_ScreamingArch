import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy

def test_hierarchy():
    print("--- Testing Hierarchy Translator ---")
    
    cases = [
        ("01", "CAOS PRIME"),
        ("0101", "ABISMO / GESTACIÓN"),
        ("010101", "UNIVERSO"), # Level 3 Physics
        ("010101010101", "PLANETA"), # Level 6 Physics (12 chars)
        ("010501010101", "CAPA / CÍRCULO"), # Level 6 Dimensional (Starts with 0105)
        
        # Level 13 (26 chars) - Biology default
        ("01010101010101010101010101", "RAZA/ESPECIE"), 
        
        # Level 13 Object (90+)
        # 12 pairs before index 24.
        # "010101010101010101010101" + "90"
        ("01010101010101010101010190", "OBJETO / ARTEFACTO"),
        
        # Level 16 Character
        ("01"*16, "PERSONAJE")
    ]
    
    for jid, expected in cases:
        result = get_readable_hierarchy(jid)
        ok = (result == expected)
        print(f"JID: {jid[:8]}... ({len(jid)//2}) | Got: {result} | Expected: {expected} | {'✅' if ok else '❌'}")

if __name__ == "__main__":
    test_hierarchy()
