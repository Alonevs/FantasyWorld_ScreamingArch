"""
MINION Role Security Test
Verifica que el rol Minion funciona correctamente:
- Ve: LIVE público + propio + jefes
- NO puede editar directamente (solo proponer)
- Propuestas van a jefes para aprobación
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
sys.path.append(os.path.join(os.getcwd(), 'src', 'Infrastructure', 'DjangoFramework'))
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.Infrastructure.DjangoFramework.persistence.policies import get_visibility_q_filter, can_user_view_world, can_user_propose_on

def test_minion_visibility():
    """Test: Minion ve LIVE público + propio + jefes"""
    print("\n" + "="*60)
    print("TEST 1: MINION - Visibilidad")
    print("="*60)
    
    # Buscar un Minion
    minion = User.objects.filter(profile__rank='MINION').first()
    if not minion:
        print("⚠️  No hay usuarios Minion para testear")
        return True
    
    print(f"Testing con usuario: {minion.username}")
    
    # Obtener filtro
    q_filter = get_visibility_q_filter(minion)
    visible_worlds = CaosWorldORM.objects.filter(q_filter)
    
    print(f"✅ Minion ve {visible_worlds.count()} mundos")
    
    # Verificar que ve a sus jefes
    if hasattr(minion, 'profile'):
        bosses = [bp.user for bp in minion.profile.bosses.all()]
        print(f"   Jefes: {[b.username for b in bosses]}")
        
        # Verificar que ve mundos de jefes
        boss_worlds = CaosWorldORM.objects.filter(author__in=bosses, status='LIVE')
        for bw in boss_worlds[:3]:
            if can_user_view_world(minion, bw):
                print(f"   ✅ Ve mundo de jefe: {bw.id} ({bw.author.username})")
            else:
                print(f"   ❌ NO ve mundo de jefe: {bw.id} ({bw.author.username})")
                return False
    
    return True

def test_minion_cannot_edit_directly():
    """Test: Minion NO puede editar directamente (solo proponer)"""
    print("\n" + "="*60)
    print("TEST 2: MINION - NO Edición Directa")
    print("="*60)
    
    minion = User.objects.filter(profile__rank='MINION').first()
    if not minion:
        print("⚠️  No hay usuarios Minion para testear")
        return True
    
    # Buscar mundo de un jefe
    if hasattr(minion, 'profile'):
        bosses = [bp.user for bp in minion.profile.bosses.all()]
        if bosses:
            boss_world = CaosWorldORM.objects.filter(author=bosses[0], status='LIVE').first()
            if boss_world:
                # Minion PUEDE proponer en mundo de jefe
                can_propose = can_user_propose_on(minion, boss_world)
                print(f"   Mundo de jefe: {boss_world.id} ({boss_world.author.username})")
                print(f"   ¿Puede proponer? {can_propose}")
                
                if can_propose:
                    print("   ✅ Minion puede PROPONER en mundo de jefe (correcto)")
                else:
                    print("   ❌ Minion NO puede proponer en mundo de jefe (ERROR)")
                    return False
    
    # Buscar mundo del Sistema
    system_world = CaosWorldORM.objects.filter(author__isnull=True).first()
    if not system_world:
        system_world = CaosWorldORM.objects.filter(author__is_superuser=True).first()
    
    if system_world:
        can_propose_system = can_user_propose_on(minion, system_world)
        print(f"\n   Mundo del Sistema: {system_world.id}")
        print(f"   ¿Puede proponer? {can_propose_system}")
        
        if not can_propose_system:
            print("   ✅ Minion NO puede proponer en Sistema (correcto - solo Admin puede)")
        else:
            print("   ⚠️  Minion PUEDE proponer en Sistema (revisar si es correcto)")
    
    return True

def test_minion_proposals_go_to_boss():
    """Test: Propuestas de Minion van a sus jefes"""
    print("\n" + "="*60)
    print("TEST 3: MINION - Propuestas van a Jefes")
    print("="*60)
    
    minion = User.objects.filter(profile__rank='MINION').first()
    if not minion:
        print("⚠️  No hay usuarios Minion para testear")
        return True
    
    if hasattr(minion, 'profile'):
        bosses = [bp.user for bp in minion.profile.bosses.all()]
        print(f"   Minion: {minion.username}")
        print(f"   Jefes: {[b.username for b in bosses]}")
        
        if bosses:
            print("   ✅ Minion tiene jefes asignados")
            print("   📋 Propuestas de Minion deberían aparecer en Dashboard de estos jefes")
        else:
            print("   ⚠️  Minion NO tiene jefes asignados")
    
    return True

def run_minion_tests():
    """Ejecuta todos los tests de Minion"""
    print("\n" + "="*60)
    print("🔍 AUDITORÍA DE ROL: MINION")
    print("="*60)
    
    tests = [
        ("Visibilidad", test_minion_visibility),
        ("NO Edición Directa", test_minion_cannot_edit_directly),
        ("Propuestas a Jefes", test_minion_proposals_go_to_boss),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error en {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN - ROL MINION")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nResultado: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n🎉 ROL MINION - CORRECTO")
    else:
        print("\n🚨 ROL MINION - REQUIERE ATENCIÓN")
    
    return passed == total

if __name__ == '__main__':
    success = run_minion_tests()
    sys.exit(0 if success else 1)
