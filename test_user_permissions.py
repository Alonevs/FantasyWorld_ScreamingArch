"""
Script de testing automatizado de permisos y accesos por rol.

Prueba que los usuarios existentes tienen acceso correcto a las vistas
según su rol asignado.

Uso:
    python test_user_permissions.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'Infrastructure', 'DjangoFramework'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory, Client
from src.Infrastructure.DjangoFramework.persistence.models import UserProfile, CaosWorldORM

print("="*70)
print("🧪 TESTING AUTOMATIZADO DE PERMISOS POR ROL")
print("="*70)

# Obtener usuarios existentes
users = User.objects.all()
print(f"\n📊 Usuarios encontrados en la base de datos: {users.count()}")

if users.count() == 0:
    print("❌ No hay usuarios en la base de datos. Crea al menos un usuario primero.")
    sys.exit(1)

print("\n" + "-"*70)
print("USUARIOS Y SUS ROLES:")
print("-"*70)

for user in users:
    try:
        profile = UserProfile.objects.get(user=user)
        rank = profile.rank
    except UserProfile.DoesNotExist:
        rank = "SIN PERFIL"
    
    is_super = "✨ SUPERUSER" if user.is_superuser else ""
    print(f"  • {user.username:20} | Rank: {rank:10} {is_super}")

print("-"*70)

# Cliente de testing
client = Client()

print("\n" + "="*70)
print("🔐 TESTING DE ACCESOS POR ROL")
print("="*70)

# URLs críticas a testear
urls_to_test = {
    'dashboard': '/dashboard/',
    'centro_control': '/centro_control/',
    'papelera': '/papelera/',
}

# Testear cada usuario
for user in users:
    print(f"\n{'='*70}")
    print(f"👤 Testing usuario: {user.username}")
    print(f"{'='*70}")
    
    # Login
    login_success = client.login(username=user.username, password='test123')
    
    if not login_success:
        print(f"⚠️  No se pudo hacer login (password incorrecto o no es 'test123')")
        print(f"   Saltando usuario {user.username}...")
        continue
    
    # Obtener rol
    try:
        profile = UserProfile.objects.get(user=user)
        rank = profile.rank
    except UserProfile.DoesNotExist:
        rank = "EXPLORER"  # Default
    
    is_super = user.is_superuser
    
    print(f"  Rol: {rank}")
    print(f"  Superuser: {'Sí' if is_super else 'No'}")
    print(f"\n  Probando accesos:")
    
    # Test Dashboard
    try:
        response = client.get('/dashboard/', SERVER_NAME='127.0.0.1')
        if response.status_code == 200:
            print(f"    ✅ /dashboard/ - ACCESO PERMITIDO (200)")
        elif response.status_code == 302:
            print(f"    🔄 /dashboard/ - REDIRIGIDO (302) → {response.url if hasattr(response, 'url') else 'login'}")
        elif response.status_code == 403:
            print(f"    ❌ /dashboard/ - ACCESO DENEGADO (403)")
        else:
            print(f"    ⚠️  /dashboard/ - Código inesperado ({response.status_code})")
    except Exception as e:
        print(f"    ❌ /dashboard/ - ERROR: {str(e)[:50]}")
    
    # Test Centro de Control
    response = client.get('/centro_control/')
    if response.status_code == 200:
        print(f"    ✅ /centro_control/ - ACCESO PERMITIDO (200)")
    elif response.status_code == 302:
        print(f"    🔄 /centro_control/ - REDIRIGIDO (302)")
    elif response.status_code == 403:
        print(f"    ❌ /centro_control/ - ACCESO DENEGADO (403)")
    else:
        print(f"    ⚠️  /centro_control/ - Código inesperado ({response.status_code})")
    
    # Test Papelera
    response = client.get('/papelera/')
    if response.status_code == 200:
        print(f"    ✅ /papelera/ - ACCESO PERMITIDO (200)")
    elif response.status_code == 302:
        print(f"    🔄 /papelera/ - REDIRIGIDO (302)")
    elif response.status_code == 403:
        print(f"    ❌ /papelera/ - ACCESO DENEGADO (403)")
    else:
        print(f"    ⚠️  /papelera/ - Código inesperado ({response.status_code})")
    
    # Verificar permisos esperados
    print(f"\n  Verificación de permisos esperados:")
    
    if is_super:
        print(f"    ✅ Superuser → Debería tener acceso a TODO")
    elif rank == 'ADMIN':
        print(f"    ✅ Admin → Debería tener acceso a Dashboard y Papelera")
    elif rank == 'SUBADMIN':
        print(f"    ⚠️  Subadmin → Acceso limitado (solo sus contribuciones)")
    elif rank == 'EXPLORER':
        print(f"    ❌ Explorer → NO debería tener acceso a Dashboard")
    
    # Logout
    client.logout()

print("\n" + "="*70)
print("✅ TESTING COMPLETADO")
print("="*70)

# Resumen
print("\n📋 RESUMEN:")
print("  - Si ves ✅ donde debería haber ❌ → HAY UN PROBLEMA DE SEGURIDAD")
print("  - Si ves ❌ donde debería haber ✅ → Usuario no tiene permisos correctos")
print("  - Los 🔄 (302) son redirecciones, normalmente a login")
print("\n")
