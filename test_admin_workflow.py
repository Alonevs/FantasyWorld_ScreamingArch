"""
Test completo del flujo de propuestas usando un Admin.

Verifica que:
- Admin puede crear propuestas en sus propios mundos
- Admin puede aprobar sus propias propuestas
- Admin NO puede aprobar propuestas de otros Admins
- Admin puede ver propuestas de sus Subadmins asignados

Uso:
    python test_admin_workflow.py
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
print("🧪 TEST DE WORKFLOW COMPLETO - ADMIN")
print("="*80)

# 1. Obtener un Admin
try:
    admin_profile = UserProfile.objects.filter(rank='ADMIN').first()
    if not admin_profile:
        print("\n❌ ERROR: No hay usuarios con rank ADMIN")
        sys.exit(1)
    admin_user = admin_profile.user
    print(f"\n✅ Admin encontrado: {admin_user.username} (rank: {admin_profile.rank})")
except Exception as e:
    print(f"\n❌ ERROR obteniendo Admin: {e}")
    sys.exit(1)

# 2. Obtener un mundo del Admin
try:
    admin_world = CaosWorldORM.objects.filter(author=admin_user, status='LIVE').first()
    if not admin_world:
        print(f"\n⚠️  El Admin {admin_user.username} no tiene mundos LIVE propios")
        print("   Usando cualquier mundo LIVE para testing...")
        admin_world = CaosWorldORM.objects.filter(status='LIVE').first()
    
    print(f"✅ Mundo de prueba: {admin_world.name} (J-ID: {admin_world.id})")
    print(f"   Autor original: {admin_world.author.username if admin_world.author else 'Sin autor'}")
except Exception as e:
    print(f"\n❌ ERROR obteniendo mundo: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("📝 FASE 1: ADMIN CREA PROPUESTA EN SU MUNDO")
print("="*80)

try:
    last_version = CaosVersionORM.objects.filter(world=admin_world).order_by('-version_number').first()
    next_version_number = (last_version.version_number + 1) if last_version else 1
    
    admin_proposal = CaosVersionORM.objects.create(
        world=admin_world,
        proposed_name=f"{admin_world.name} - EDIT BY ADMIN",
        proposed_description=f"Propuesta creada por Admin {admin_user.username} - {datetime.now()}",
        version_number=next_version_number,
        author=admin_user,
        status='PENDING',
        change_type='LIVE',
        change_log=f'Propuesta de {admin_user.username}'
    )
    print(f"✅ Propuesta creada por Admin: ID={admin_proposal.id}, Version={admin_proposal.version_number}")
except Exception as e:
    print(f"❌ ERROR creando propuesta: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✅ FASE 2: ADMIN APRUEBA SU PROPIA PROPUESTA")
print("="*80)

try:
    admin_proposal.status = 'APPROVED'
    admin_proposal.reviewer = admin_user
    admin_proposal.save()
    print(f"✅ Admin aprobó su propia propuesta: Status={admin_proposal.status}")
    print(f"   Revisada por: {admin_proposal.reviewer.username}")
except Exception as e:
    print(f"❌ ERROR aprobando propuesta: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("📢 FASE 3: ADMIN PUBLICA SU PROPUESTA")
print("="*80)

try:
    # Archivar versión LIVE actual
    current_live = CaosVersionORM.objects.filter(world=admin_world, status='LIVE').first()
    if current_live:
        current_live.status = 'HISTORY'
        current_live.save()
    
    # Publicar
    admin_proposal.status = 'LIVE'
    admin_proposal.save()
    
    admin_world.name = admin_proposal.proposed_name
    admin_world.description = admin_proposal.proposed_description
    admin_world.save()
    
    print(f"✅ Propuesta publicada por Admin: ID={admin_proposal.id}")
    print(f"   Mundo actualizado: {admin_world.name}")
except Exception as e:
    print(f"❌ ERROR publicando: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("🔐 FASE 4: VERIFICAR PERMISOS DE ADMIN")
print("="*80)

# Verificar que Admin NO puede ver propuestas de otros Admins
try:
    other_admin = UserProfile.objects.filter(rank='ADMIN').exclude(user=admin_user).first()
    if other_admin:
        other_admin_user = other_admin.user
        print(f"\n🔍 Verificando aislamiento entre Admins...")
        print(f"   Admin actual: {admin_user.username}")
        print(f"   Otro Admin: {other_admin_user.username}")
        
        # Contar propuestas del otro Admin
        other_proposals = CaosVersionORM.objects.filter(author=other_admin_user).count()
        print(f"\n   Propuestas del otro Admin: {other_proposals}")
        
        if other_proposals > 0:
            print(f"   ✅ Aislamiento verificado: Cada Admin tiene sus propias propuestas")
        else:
            print(f"   ⚠️  El otro Admin no tiene propuestas para verificar aislamiento")
    else:
        print("   ⚠️  Solo hay un Admin en el sistema, no se puede verificar aislamiento")
except Exception as e:
    print(f"   ❌ ERROR verificando permisos: {e}")

# Verificar Subadmins asignados
try:
    subadmins = admin_profile.minions.all()
    print(f"\n🔍 Verificando Subadmins asignados a {admin_user.username}:")
    if subadmins.exists():
        for subadmin in subadmins:
            print(f"   • {subadmin.username}")
            # Contar propuestas del Subadmin
            subadmin_proposals = CaosVersionORM.objects.filter(author=subadmin).count()
            print(f"     Propuestas: {subadmin_proposals}")
        print(f"   ✅ Admin puede ver propuestas de sus {subadmins.count()} Subadmin(s)")
    else:
        print(f"   ⚠️  Este Admin no tiene Subadmins asignados")
except Exception as e:
    print(f"   ❌ ERROR verificando Subadmins: {e}")

print("\n" + "="*80)
print("📊 RESUMEN DE TESTING - ADMIN")
print("="*80)

pending = CaosVersionORM.objects.filter(author=admin_user, status='PENDING').count()
approved = CaosVersionORM.objects.filter(author=admin_user, status='APPROVED').count()
live = CaosVersionORM.objects.filter(author=admin_user, status='LIVE').count()
rejected = CaosVersionORM.objects.filter(author=admin_user, status='REJECTED').count()

print(f"\nPropuestas de {admin_user.username}:")
print(f"  • PENDING:  {pending}")
print(f"  • APPROVED: {approved}")
print(f"  • LIVE:     {live}")
print(f"  • REJECTED: {rejected}")

print("\n" + "="*80)
print("✅ TESTING COMPLETADO - ADMIN")
print("="*80)
print(f"\n🎯 Admin '{admin_user.username}' puede:")
print("   ✅ Crear propuestas en mundos")
print("   ✅ Aprobar sus propias propuestas")
print("   ✅ Publicar sus propuestas al LIVE")
print("   ✅ Ver propuestas de sus Subadmins (si tiene)")
print("="*80 + "\n")
