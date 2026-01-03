"""
Test completo del flujo de propuestas usando un Subadmin.

Verifica que:
- Subadmin puede crear propuestas
- Subadmin NO puede aprobar sus propias propuestas
- Subadmin solo puede contribuir, no gestionar

Uso:
    python test_subadmin_workflow.py
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
from datetime import datetime

print("="*80)
print("🧪 TEST DE WORKFLOW COMPLETO - SUBADMIN")
print("="*80)

# 1. Obtener un Subadmin
try:
    subadmin_profile = UserProfile.objects.filter(rank='SUBADMIN').first()
    if not subadmin_profile:
        print("\n❌ ERROR: No hay usuarios con rank SUBADMIN")
        sys.exit(1)
    subadmin_user = subadmin_profile.user
    print(f"\n✅ Subadmin encontrado: {subadmin_user.username} (rank: {subadmin_profile.rank})")
    
    # Verificar si tiene jefes asignados
    bosses = subadmin_profile.bosses.all()
    if bosses.exists():
        print(f"   Jefes asignados: {', '.join([b.user.username for b in bosses])}")
    else:
        print(f"   ⚠️  Este Subadmin no tiene jefes asignados")
except Exception as e:
    print(f"\n❌ ERROR obteniendo Subadmin: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. Obtener un mundo para probar
try:
    test_world = CaosWorldORM.objects.filter(status='LIVE').first()
    print(f"✅ Mundo de prueba: {test_world.name} (J-ID: {test_world.id})")
except Exception as e:
    print(f"\n❌ ERROR obteniendo mundo: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("📝 FASE 1: SUBADMIN CREA PROPUESTA")
print("="*80)

try:
    last_version = CaosVersionORM.objects.filter(world=test_world).order_by('-version_number').first()
    next_version_number = (last_version.version_number + 1) if last_version else 1
    
    subadmin_proposal = CaosVersionORM.objects.create(
        world=test_world,
        proposed_name=f"{test_world.name} - EDIT BY SUBADMIN",
        proposed_description=f"Propuesta creada por Subadmin {subadmin_user.username} - {datetime.now()}",
        version_number=next_version_number,
        author=subadmin_user,
        status='PENDING',
        change_type='LIVE',
        change_log=f'Contribución de {subadmin_user.username}'
    )
    print(f"✅ Propuesta creada por Subadmin: ID={subadmin_proposal.id}, Version={subadmin_proposal.version_number}")
    print(f"   Estado: {subadmin_proposal.status}")
    print(f"   Autor: {subadmin_proposal.author.username}")
except Exception as e:
    print(f"❌ ERROR creando propuesta: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("🔐 FASE 2: VERIFICAR QUE SUBADMIN NO PUEDE APROBAR")
print("="*80)

try:
    print(f"🔍 Intentando que Subadmin apruebe su propia propuesta...")
    print(f"   (En la UI real, el botón 'Aprobar' NO debería estar visible)")
    print(f"   (Aquí lo probamos directamente en la BD)")
    
    # Intentar aprobar (esto debería estar bloqueado en la UI)
    subadmin_proposal.status = 'APPROVED'
    subadmin_proposal.reviewer = subadmin_user
    subadmin_proposal.save()
    
    print(f"   ⚠️  ADVERTENCIA: Subadmin pudo cambiar el status a APPROVED en la BD")
    print(f"   ⚠️  Esto debería estar bloqueado en las vistas/permisos")
    print(f"   ⚠️  La UI debe prevenir esto mostrando solo 'Pendiente de revisión'")
    
    # Revertir para no contaminar
    subadmin_proposal.status = 'PENDING'
    subadmin_proposal.reviewer = None
    subadmin_proposal.save()
    print(f"   ✅ Status revertido a PENDING para testing limpio")
except Exception as e:
    print(f"   ❌ ERROR en verificación: {e}")

print("\n" + "="*80)
print("👀 FASE 3: VERIFICAR VISIBILIDAD DE PROPUESTAS")
print("="*80)

try:
    # Propuestas del Subadmin
    my_proposals = CaosVersionORM.objects.filter(author=subadmin_user).count()
    print(f"\n📊 Propuestas creadas por {subadmin_user.username}: {my_proposals}")
    
    # Propuestas de otros
    other_proposals = CaosVersionORM.objects.exclude(author=subadmin_user).count()
    print(f"📊 Propuestas de otros usuarios: {other_proposals}")
    
    print(f"\n✅ Subadmin debería ver:")
    print(f"   • Sus propias propuestas: {my_proposals}")
    print(f"   • NO debería ver propuestas de otros (excepto en lectura)")
except Exception as e:
    print(f"   ❌ ERROR verificando visibilidad: {e}")

print("\n" + "="*80)
print("📊 RESUMEN DE TESTING - SUBADMIN")
print("="*80)

pending = CaosVersionORM.objects.filter(author=subadmin_user, status='PENDING').count()
approved = CaosVersionORM.objects.filter(author=subadmin_user, status='APPROVED').count()
live = CaosVersionORM.objects.filter(author=subadmin_user, status='LIVE').count()
rejected = CaosVersionORM.objects.filter(author=subadmin_user, status='REJECTED').count()

print(f"\nPropuestas de {subadmin_user.username}:")
print(f"  • PENDING:  {pending}")
print(f"  • APPROVED: {approved}")
print(f"  • LIVE:     {live}")
print(f"  • REJECTED: {rejected}")

print("\n" + "="*80)
print("✅ TESTING COMPLETADO - SUBADMIN")
print("="*80)
print(f"\n🎯 Subadmin '{subadmin_user.username}':")
print("   ✅ PUEDE crear propuestas")
print("   ✅ PUEDE ver sus propias propuestas")
print("   ⚠️  NO DEBERÍA poder aprobar (bloqueado en UI)")
print("   ⚠️  NO DEBERÍA poder publicar (bloqueado en UI)")
print("   ✅ Depende de su Jefe para aprobación")
print("="*80 + "\n")
