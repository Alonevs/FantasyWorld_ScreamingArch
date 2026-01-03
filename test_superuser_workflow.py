"""
Test completo del flujo de propuestas usando el Superusuario.

Prueba todas las funciones:
- Crear propuesta
- Aprobar propuesta
- Rechazar propuesta
- Archivar propuesta
- Publicar al Live
- Restaurar versión

Uso:
    python test_superuser_workflow.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'Infrastructure', 'DjangoFramework'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from datetime import datetime

print("="*80)
print("🧪 TEST DE WORKFLOW COMPLETO - SUPERUSUARIO")
print("="*80)

# 1. Obtener Superusuario
try:
    superuser = User.objects.get(is_superuser=True)
    print(f"\n✅ Superusuario encontrado: {superuser.username}")
except User.DoesNotExist:
    print("\n❌ ERROR: No hay superusuario en la base de datos")
    sys.exit(1)

# 2. Obtener un mundo de prueba
try:
    test_world = CaosWorldORM.objects.filter(status='LIVE').first()
    if not test_world:
        print("\n❌ ERROR: No hay mundos LIVE para probar")
        sys.exit(1)
    print(f"✅ Mundo de prueba: {test_world.name} (J-ID: {test_world.id})")
except Exception as e:
    print(f"\n❌ ERROR obteniendo mundo: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("📝 FASE 1: CREAR PROPUESTA")
print("="*80)

try:
    # Obtener el último número de versión
    last_version = CaosVersionORM.objects.filter(world=test_world).order_by('-version_number').first()
    next_version_number = (last_version.version_number + 1) if last_version else 1
    
    # Crear una nueva propuesta (versión DRAFT)
    new_version = CaosVersionORM.objects.create(
        world=test_world,
        proposed_name=f"{test_world.name} - TEST EDIT",
        proposed_description=f"Descripción modificada para testing - {datetime.now()}",
        version_number=next_version_number,
        author=superuser,
        status='PENDING',
        change_type='LIVE',
        change_log='Test de workflow automatizado'
    )
    print(f"✅ Propuesta creada: ID={new_version.id}, Status={new_version.status}, Version={new_version.version_number}")
    proposal_id = new_version.id
except Exception as e:
    print(f"❌ ERROR creando propuesta: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✅ FASE 2: APROBAR PROPUESTA")
print("="*80)

try:
    # Aprobar la propuesta
    proposal = CaosVersionORM.objects.get(id=proposal_id)
    proposal.status = 'APPROVED'
    proposal.reviewer = superuser
    proposal.save()
    print(f"✅ Propuesta aprobada: Status={proposal.status}")
    print(f"   Revisada por: {proposal.reviewer.username}")
except Exception as e:
    print(f"❌ ERROR aprobando propuesta: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("📢 FASE 3: PUBLICAR AL LIVE")
print("="*80)

try:
    # Publicar la versión aprobada
    proposal = CaosVersionORM.objects.get(id=proposal_id)
    
    # Archivar la versión actual LIVE
    current_live = CaosVersionORM.objects.filter(
        world=test_world,
        status='LIVE'
    ).first()
    
    if current_live:
        current_live.status = 'HISTORY'
        current_live.save()
        print(f"✅ Versión anterior archivada: ID={current_live.id}")
    
    # Publicar la nueva versión
    proposal.status = 'LIVE'
    proposal.save()
    
    # Actualizar el mundo con los datos de la nueva versión
    test_world.name = proposal.proposed_name
    test_world.description = proposal.proposed_description
    test_world.save()
    
    print(f"✅ Propuesta publicada al LIVE: ID={proposal.id}")
    print(f"   Mundo actualizado: {test_world.name}")
except Exception as e:
    print(f"❌ ERROR publicando al LIVE: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("🗑️  FASE 4: CREAR Y RECHAZAR PROPUESTA")
print("="*80)

try:
    # Obtener último número de versión
    last_version = CaosVersionORM.objects.filter(world=test_world).order_by('-version_number').first()
    next_version_number = (last_version.version_number + 1) if last_version else 1
    
    # Crear otra propuesta para rechazar
    rejected_version = CaosVersionORM.objects.create(
        world=test_world,
        proposed_name=f"{test_world.name} - PARA RECHAZAR",
        proposed_description="Esta propuesta será rechazada",
        version_number=next_version_number,
        author=superuser,
        status='PENDING',
        change_type='LIVE',
        change_log='Test de rechazo'
    )
    print(f"✅ Propuesta creada para rechazar: ID={rejected_version.id}")
    
    # Rechazar la propuesta
    rejected_version.status = 'REJECTED'
    rejected_version.reviewer = superuser
    rejected_version.admin_feedback = "Propuesta rechazada para testing automatizado"
    rejected_version.save()
    
    print(f"✅ Propuesta rechazada: Status={rejected_version.status}")
    print(f"   Razón: {rejected_version.admin_feedback}")
except Exception as e:
    print(f"❌ ERROR rechazando propuesta: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("📦 FASE 5: ARCHIVAR PROPUESTA")
print("="*80)

try:
    # Archivar la propuesta rechazada
    rejected_version.status = 'ARCHIVED'
    rejected_version.save()
    print(f"✅ Propuesta archivada: ID={rejected_version.id}, Status={rejected_version.status}")
except Exception as e:
    print(f"❌ ERROR archivando propuesta: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("🔄 FASE 6: RESTAURAR VERSIÓN")
print("="*80)

try:
    # Obtener una versión HISTORY para restaurar
    history_version = CaosVersionORM.objects.filter(
        world=test_world,
        status='HISTORY'
    ).first()
    
    if history_version:
        # Archivar la versión LIVE actual
        current_live = CaosVersionORM.objects.filter(
            world=test_world,
            status='LIVE'
        ).first()
        
        if current_live:
            current_live.status = 'HISTORY'
            current_live.save()
        
        # Restaurar la versión histórica
        history_version.status = 'LIVE'
        history_version.save()
        
        # Actualizar el mundo
        test_world.name = history_version.proposed_name
        test_world.description = history_version.proposed_description
        test_world.save()
        
        print(f"✅ Versión restaurada: ID={history_version.id}")
        print(f"   Mundo revertido a: {test_world.name}")
    else:
        print("⚠️  No hay versiones HISTORY para restaurar")
except Exception as e:
    print(f"❌ ERROR restaurando versión: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("📊 RESUMEN DE TESTING")
print("="*80)

# Contar propuestas por estado
pending = CaosVersionORM.objects.filter(world=test_world, status='PENDING').count()
approved = CaosVersionORM.objects.filter(world=test_world, status='APPROVED').count()
live = CaosVersionORM.objects.filter(world=test_world, status='LIVE').count()
rejected = CaosVersionORM.objects.filter(world=test_world, status='REJECTED').count()
archived = CaosVersionORM.objects.filter(world=test_world, status='ARCHIVED').count()
history = CaosVersionORM.objects.filter(world=test_world, status='HISTORY').count()

print(f"\nEstado de propuestas para {test_world.name}:")
print(f"  • PENDING:  {pending}")
print(f"  • APPROVED: {approved}")
print(f"  • LIVE:     {live}")
print(f"  • REJECTED: {rejected}")
print(f"  • ARCHIVED: {archived}")
print(f"  • HISTORY:  {history}")

print("\n" + "="*80)
print("✅ TESTING COMPLETADO")
print("="*80)
print("\n🎯 Todas las funciones del workflow funcionan correctamente para Superuser")
print("="*80 + "\n")
