
import os
import sys
import django

# Setup Django Environment
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src')) 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase

def test_leak():
    print("🚀 TEST: Debugging Leakage (Grandchild Visibility)")
    
    # Setup
    root = '77'
    parent = '7701'
    child = '770101'
    
    # Cleanup
    CaosWorldORM.objects.filter(id__startswith='77').delete()
    
    print("📋 Creando jerarquía: 77 -> 7701 -> 770101 (Todos Real/Live)")
    CaosWorldORM.objects.create(id=root, name="Root 77", status='LIVE', is_active=True, visible_publico=True)
    CaosWorldORM.objects.create(id=parent, name="Parent 7701", status='LIVE', is_active=True, visible_publico=True)
    CaosWorldORM.objects.create(id=child, name="Child 770101", status='LIVE', is_active=True, visible_publico=True)
    
    repo = DjangoCaosRepository()
    use_case = GetWorldDetailsUseCase(repo)
    
    print(f"\n🔍 Viendo ROOT '{root}'...")
    try:
        details = use_case.execute(root, user=None)
        children = details['hijos']
        child_ids = [c['id'] for c in children]
        
        print(f"    Hijos visibles: {child_ids}")
        
        # Expectation: Should see 7701. Should NOT see 770101.
        if parent in child_ids and child not in child_ids:
            print(f"    ✅ CORRECTO: Solo ve al Padre. El Nieto está oculto.")
        else:
            print(f"    ❌ FALLO: Visibilidad incorrecta.")
            if child in child_ids:
                print(f"       -> 🚨 LEAK: El Nieto {child} es visible en el Root!")
                
    except Exception as e:
        print(f"    ❌ ERROR EJECUCION: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    print("\n🧹 Limpiando...")
    CaosWorldORM.objects.filter(id__startswith='77').delete()
    print("✨ Test Finalizado.")

if __name__ == "__main__":
    test_leak()
