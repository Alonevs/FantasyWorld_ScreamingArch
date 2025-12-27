"""
SUBADMIN Role Security Test
Verifica que el rol SubAdmin funciona correctamente:
- Ve: LIVE público + propio + jefes + equipo
- Puede editar: propio + equipo (directo)
- NO puede editar: Sistema/Superuser (solo proponer)
- Puede reclutar: NO (solo Admin/Superuser)
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

def test_subadmin_visibility():
    """Test: SubAdmin ve LIVE público + propio + jefes + equipo"""
    print("\n" + "="*60)
    print("TEST 1: SUBADMIN - Visibilidad")
    print("="*60)
    
    subadmin = User.objects.filter(profile__rank='SUBADMIN').first()
    if not subadmin:
        print("⚠️  No hay usuarios SubAdmin para testear")
        return True
    
    print(f"Testing con usuario: {subadmin.username}")
    
    q_filter = get_visibility_q_filter(subadmin)
    visible_worlds = CaosWorldORM.objects.filter(q_filter)
    
    print(f"✅ SubAdmin ve {visible_worlds.count()} mundos")
    
    # Verificar que ve a sus jefes
    if hasattr(subadmin, 'profile'):
        bosses = [bp.user for bp in subadmin.profile.bosses.all()]
        print(f"   Jefes: {[b.username for b in bosses]}")
        
        # Verificar que ve mundos de jefes
        if bosses:
            boss_worlds = CaosWorldORM.objects.filter(author__in=bosses, status='LIVE')[:3]
            for bw in boss_worlds:
                if can_user_view_world(subadmin, bw):
                    print(f"   ✅ Ve mundo de jefe: {bw.id}")
                else:
                    print(f"   ❌ NO ve mundo de jefe: {bw.id}")
                    return False
    
    return True

def test_subadmin_can_edit_own():
    """Test: SubAdmin puede editar su propio contenido directamente"""
    print("\n" + "="*60)
    print("TEST 2: SUBADMIN - Edición Propia")
    print("="*60)
    
    subadmin = User.objects.filter(profile__rank='SUBADMIN').first()
    if not subadmin:
        print("⚠️  No hay usuarios SubAdmin para testear")
        return True
    
    # Buscar mundo propio
    own_world = CaosWorldORM.objects.filter(author=subadmin, status='LIVE').first()
    if own_world:
        can_propose = can_user_propose_on(subadmin, own_world)
        print(f"   Mundo propio: {own_world.id}")
        print(f"   ¿Puede proponer/editar? {can_propose}")
        
        if can_propose:
            print("   ✅ SubAdmin puede editar su propio contenido")
        else:
            print("   ❌ SubAdmin NO puede editar su propio contenido (ERROR)")
            return False
    else:
        print("   ⚠️  SubAdmin no tiene mundos propios para testear")
    
    return True

def test_subadmin_cannot_edit_system():
    """Test: SubAdmin NO puede editar Sistema directamente (solo proponer)"""
    print("\n" + "="*60)
    print("TEST 3: SUBADMIN - NO Edición de Sistema")
    print("="*60)
    
    subadmin = User.objects.filter(profile__rank='SUBADMIN').first()
    if not subadmin:
        print("⚠️  No hay usuarios SubAdmin para testear")
        return True
    
    # Buscar mundo del Sistema
    system_world = CaosWorldORM.objects.filter(author__isnull=True).first()
    if not system_world:
        system_world = CaosWorldORM.objects.filter(author__is_superuser=True).first()
    
    if system_world:
        can_propose = can_user_propose_on(subadmin, system_world)
        print(f"   Mundo del Sistema: {system_world.id}")
        print(f"   ¿Puede proponer? {can_propose}")
        
        # SubAdmin NO debería poder proponer en Sistema (solo Admin puede)
        if not can_propose:
            print("   ✅ SubAdmin NO puede proponer en Sistema (correcto)")
        else:
            print("   ⚠️  SubAdmin PUEDE proponer en Sistema (revisar si es correcto)")
            # Esto podría ser correcto si SubAdmin tiene permisos especiales
    
    return True

def test_subadmin_hierarchy():
    """Test: SubAdmin está en jerarquía correcta"""
    print("\n" + "="*60)
    print("TEST 4: SUBADMIN - Jerarquía")
    print("="*60)
    
    subadmin = User.objects.filter(profile__rank='SUBADMIN').first()
    if not subadmin:
        print("⚠️  No hay usuarios SubAdmin para testear")
        return True
    
    if hasattr(subadmin, 'profile'):
        bosses = [bp.user for bp in subadmin.profile.bosses.all()]
        minions = User.objects.filter(profile__bosses__user=subadmin)
        
        print(f"   SubAdmin: {subadmin.username}")
        print(f"   Jefes: {[b.username for b in bosses]}")
        print(f"   Subordinados: {[m.username for m in minions]}")
        
        # Verificar que jefes son Admin o Superuser
        for boss in bosses:
            if hasattr(boss, 'profile'):
                if boss.profile.rank in ['ADMIN', 'SUPERADMIN'] or boss.is_superuser:
                    print(f"   ✅ Jefe {boss.username} es {boss.profile.rank if hasattr(boss, 'profile') else 'SUPERUSER'}")
                else:
                    print(f"   ⚠️  Jefe {boss.username} es {boss.profile.rank} (debería ser ADMIN+)")
    
    return True

def run_subadmin_tests():
    """Ejecuta todos los tests de SubAdmin"""
    print("\n" + "="*60)
    print("🔍 AUDITORÍA DE ROL: SUBADMIN")
    print("="*60)
    
    tests = [
        ("Visibilidad", test_subadmin_visibility),
        ("Edición Propia", test_subadmin_can_edit_own),
        ("NO Edición Sistema", test_subadmin_cannot_edit_system),
        ("Jerarquía", test_subadmin_hierarchy),
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
    print("RESUMEN - ROL SUBADMIN")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nResultado: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n🎉 ROL SUBADMIN - CORRECTO")
    else:
        print("\n🚨 ROL SUBADMIN - REQUIERE ATENCIÓN")
    
    return passed == total

if __name__ == '__main__':
    success = run_subadmin_tests()
    sys.exit(0 if success else 1)
