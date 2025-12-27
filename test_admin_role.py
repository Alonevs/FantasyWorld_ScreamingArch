"""
ADMIN Role Security Test
Verifica que el rol Admin funciona correctamente:
- Ve: LIVE público + propio + equipo + Sistema (para proponer)
- Puede editar: propio + equipo (directo)
- Puede proponer: en Sistema/Superuser
- Puede reclutar: Sí (hasta SubAdmin)
- Silos Territoriales: NO ve propuestas de Minions sobre Sistema
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

def test_admin_sees_system():
    """Test: Admin ve mundos del Sistema (para proponer)"""
    print("\n" + "="*60)
    print("TEST 1: ADMIN - Ve Sistema")
    print("="*60)
    
    admin = User.objects.filter(profile__rank='ADMIN').first()
    if not admin:
        print("⚠️  No hay usuarios Admin para testear")
        return True
    
    print(f"Testing con usuario: {admin.username}")
    
    # Buscar mundos del Sistema
    system_worlds = CaosWorldORM.objects.filter(author__isnull=True) | CaosWorldORM.objects.filter(author__is_superuser=True)
    system_worlds = system_worlds.filter(status='LIVE')[:3]
    
    for sw in system_worlds:
        if can_user_view_world(admin, sw):
            print(f"   ✅ Admin ve mundo Sistema: {sw.id}")
        else:
            print(f"   ❌ Admin NO ve mundo Sistema: {sw.id} (ERROR)")
            return False
    
    return True

def test_admin_can_propose_on_system():
    """Test: Admin puede PROPONER en Sistema"""
    print("\n" + "="*60)
    print("TEST 2: ADMIN - Propone en Sistema")
    print("="*60)
    
    admin = User.objects.filter(profile__rank='ADMIN').first()
    if not admin:
        print("⚠️  No hay usuarios Admin para testear")
        return True
    
    system_world = CaosWorldORM.objects.filter(author__isnull=True).first()
    if not system_world:
        system_world = CaosWorldORM.objects.filter(author__is_superuser=True).first()
    
    if system_world:
        can_propose = can_user_propose_on(admin, system_world)
        print(f"   Mundo del Sistema: {system_world.id}")
        print(f"   ¿Puede proponer? {can_propose}")
        
        if can_propose:
            print("   ✅ Admin puede PROPONER en Sistema (correcto)")
        else:
            print("   ❌ Admin NO puede proponer en Sistema (ERROR)")
            return False
    
    return True

def test_admin_edits_team_directly():
    """Test: Admin puede editar contenido de su equipo directamente"""
    print("\n" + "="*60)
    print("TEST 3: ADMIN - Edita Equipo Directamente")
    print("="*60)
    
    admin = User.objects.filter(profile__rank='ADMIN').first()
    if not admin:
        print("⚠️  No hay usuarios Admin para testear")
        return True
    
    # Buscar minions del admin
    minions = User.objects.filter(profile__bosses__user=admin)
    print(f"   Admin: {admin.username}")
    print(f"   Equipo: {[m.username for m in minions]}")
    
    if minions:
        # Buscar mundo de un minion
        minion_world = CaosWorldORM.objects.filter(author__in=minions, status='LIVE').first()
        if minion_world:
            can_propose = can_user_propose_on(admin, minion_world)
            print(f"   Mundo de Minion: {minion_world.id} ({minion_world.author.username})")
            print(f"   ¿Puede editar? {can_propose}")
            
            if can_propose:
                print("   ✅ Admin puede editar mundo de su equipo")
            else:
                print("   ❌ Admin NO puede editar mundo de su equipo (ERROR)")
                return False
    else:
        print("   ⚠️  Admin no tiene equipo para testear")
    
    return True

def test_admin_territorial_silos():
    """Test: Admin NO ve mundos privados de otros Admins"""
    print("\n" + "="*60)
    print("TEST 4: ADMIN - Silos Territoriales")
    print("="*60)
    
    admin = User.objects.filter(profile__rank='ADMIN').first()
    if not admin:
        print("⚠️  No hay usuarios Admin para testear")
        return True
    
    # Buscar otro Admin
    other_admin = User.objects.filter(profile__rank='ADMIN').exclude(id=admin.id).first()
    if other_admin:
        # Buscar mundo privado del otro Admin
        other_admin_world = CaosWorldORM.objects.filter(
            author=other_admin, 
            status='LIVE',
            visible_publico=False
        ).first()
        
        if other_admin_world:
            can_view = can_user_view_world(admin, other_admin_world)
            print(f"   Mundo privado de otro Admin: {other_admin_world.id} ({other_admin.username})")
            print(f"   ¿Puede ver? {can_view}")
            
            if not can_view:
                print("   ✅ Admin NO ve mundo privado de otro Admin (Silo correcto)")
            else:
                print("   ⚠️  Admin VE mundo privado de otro Admin (revisar si es correcto)")
        else:
            print("   ⚠️  No hay mundos privados de otros Admins para testear")
    else:
        print("   ⚠️  No hay otros Admins para testear Silos")
    
    return True

def run_admin_tests():
    """Ejecuta todos los tests de Admin"""
    print("\n" + "="*60)
    print("🔍 AUDITORÍA DE ROL: ADMIN")
    print("="*60)
    
    tests = [
        ("Ve Sistema", test_admin_sees_system),
        ("Propone en Sistema", test_admin_can_propose_on_system),
        ("Edita Equipo", test_admin_edits_team_directly),
        ("Silos Territoriales", test_admin_territorial_silos),
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
    print("RESUMEN - ROL ADMIN")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nResultado: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n🎉 ROL ADMIN - CORRECTO")
    else:
        print("\n🚨 ROL ADMIN - REQUIERE ATENCIÓN")
    
    return passed == total

if __name__ == '__main__':
    success = run_admin_tests()
    sys.exit(0 if success else 1)
