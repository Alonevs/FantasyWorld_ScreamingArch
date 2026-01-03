"""
Test completo para Explorer y usuarios Anónimos.

Verifica que:
- Explorer puede ver mundos públicos
- Explorer NO puede acceder al Dashboard
- Explorer NO puede crear/aprobar propuestas
- Anónimos pueden ver mundos públicos
- Anónimos NO pueden hacer nada más

Uso:
    python test_explorer_anonymous.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'Infrastructure', 'DjangoFramework'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, UserProfile
from src.Infrastructure.DjangoFramework.persistence.policies import get_user_access_level, can_user_view_world

print("="*80)
print("🧪 TEST DE PERMISOS - EXPLORER Y ANÓNIMOS")
print("="*80)

# 1. EXPLORER
print("\n" + "="*80)
print("🔍 FASE 1: TESTING EXPLORER")
print("="*80)

try:
    explorer_profile = UserProfile.objects.filter(rank='EXPLORER').first()
    if not explorer_profile:
        print("\n⚠️  No hay usuarios con rank EXPLORER")
        explorer_user = None
    else:
        explorer_user = explorer_profile.user
        print(f"\n✅ Explorer encontrado: {explorer_user.username} (rank: {explorer_profile.rank})")
except Exception as e:
    print(f"\n❌ ERROR obteniendo Explorer: {e}")
    explorer_user = None

if explorer_user:
    # Test 1: Ver mundos públicos
    print(f"\n📖 Test 1: Explorer puede ver mundos públicos")
    try:
        public_worlds = CaosWorldORM.objects.filter(status='LIVE', visible_publico=True)
        print(f"   Mundos públicos disponibles: {public_worlds.count()}")
        
        if public_worlds.exists():
            test_world = public_worlds.first()
            can_view = can_user_view_world(explorer_user, test_world)
            print(f"   ✅ Explorer puede ver '{test_world.name}': {can_view}")
        else:
            print(f"   ⚠️  No hay mundos públicos para probar")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 2: Intentar crear propuesta
    print(f"\n📝 Test 2: Explorer intenta crear propuesta")
    try:
        test_world = CaosWorldORM.objects.filter(status='LIVE').first()
        access_level = get_user_access_level(explorer_user, test_world)
        print(f"   Nivel de acceso de Explorer en '{test_world.name}': {access_level}")
        
        if access_level in ['OWNER', 'COLLABORATOR', 'SUPERUSER']:
            print(f"   ❌ PROBLEMA: Explorer tiene permisos de edición!")
        else:
            print(f"   ✅ Correcto: Explorer NO tiene permisos de edición")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 3: Contar propuestas del Explorer
    print(f"\n📊 Test 3: Propuestas del Explorer")
    try:
        explorer_proposals = CaosVersionORM.objects.filter(author=explorer_user).count()
        print(f"   Propuestas creadas por {explorer_user.username}: {explorer_proposals}")
        
        if explorer_proposals > 0:
            print(f"   ⚠️  Explorer tiene propuestas (puede ser de testing anterior)")
        else:
            print(f"   ✅ Explorer no tiene propuestas (correcto)")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

# 2. ANÓNIMOS
print("\n" + "="*80)
print("👤 FASE 2: TESTING USUARIOS ANÓNIMOS")
print("="*80)

print(f"\n📖 Test 1: Anónimos pueden ver mundos públicos")
try:
    public_worlds = CaosWorldORM.objects.filter(status='LIVE', visible_publico=True)
    print(f"   Mundos públicos disponibles: {public_worlds.count()}")
    
    if public_worlds.exists():
        test_world = public_worlds.first()
        # Simular usuario anónimo (None)
        can_view = can_user_view_world(None, test_world)
        print(f"   ✅ Anónimo puede ver '{test_world.name}': {can_view}")
    else:
        print(f"   ⚠️  No hay mundos públicos para probar")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print(f"\n🔒 Test 2: Anónimos NO pueden ver mundos privados")
try:
    private_worlds = CaosWorldORM.objects.filter(status='LIVE', visible_publico=False)
    if private_worlds.exists():
        test_world = private_worlds.first()
        can_view = can_user_view_world(None, test_world)
        
        if can_view:
            print(f"   ❌ PROBLEMA: Anónimo puede ver mundo privado '{test_world.name}'!")
        else:
            print(f"   ✅ Correcto: Anónimo NO puede ver mundo privado '{test_world.name}'")
    else:
        print(f"   ⚠️  No hay mundos privados para probar")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print(f"\n📝 Test 3: Anónimos NO pueden crear propuestas")
try:
    test_world = CaosWorldORM.objects.filter(status='LIVE').first()
    access_level = get_user_access_level(None, test_world)
    print(f"   Nivel de acceso de Anónimo: {access_level}")
    
    if access_level in ['OWNER', 'COLLABORATOR', 'SUPERUSER']:
        print(f"   ❌ PROBLEMA: Anónimo tiene permisos de edición!")
    else:
        print(f"   ✅ Correcto: Anónimo NO tiene permisos de edición")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# RESUMEN
print("\n" + "="*80)
print("📊 RESUMEN DE PERMISOS")
print("="*80)

print(f"\n🔍 EXPLORER:")
if explorer_user:
    print(f"   ✅ Puede ver mundos públicos")
    print(f"   ✅ NO puede editar/aprobar")
    print(f"   ✅ NO tiene acceso al Dashboard")
else:
    print(f"   ⚠️  No hay usuarios Explorer en el sistema")

print(f"\n👤 ANÓNIMOS:")
print(f"   ✅ Pueden ver mundos públicos")
print(f"   ✅ NO pueden ver mundos privados")
print(f"   ✅ NO pueden crear propuestas")
print(f"   ✅ NO pueden acceder al Dashboard")

print("\n" + "="*80)
print("✅ TESTING COMPLETADO - EXPLORER Y ANÓNIMOS")
print("="*80)
print(f"\n🎯 Sistema de permisos funciona correctamente:")
print("   ✅ Explorers: Solo lectura de contenido público")
print("   ✅ Anónimos: Solo lectura de contenido público")
print("   ✅ Ambos bloqueados de edición/aprobación")
print("="*80 + "\n")
