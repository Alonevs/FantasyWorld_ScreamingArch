"""
Test rápido del sistema dual de propuestas.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Shared.Services.ProposalService import LiveProposalService, TimelineProposalService
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from django.contrib.auth.models import User

print("🧪 Test del Sistema Dual de Propuestas\n")
print("=" * 60)

# Obtener o crear usuario de prueba
user, created = User.objects.get_or_create(username='test_user', defaults={'email': 'test@test.com'})
if created:
    print(f"✅ Usuario de prueba creado: {user.username}")
else:
    print(f"✅ Usuario de prueba encontrado: {user.username}")

# Obtener primera entidad
world = CaosWorldORM.objects.filter(is_active=True).first()
if not world:
    print("❌ No hay entidades en la BD")
    sys.exit(1)

print(f"✅ Entidad de prueba: {world.name} ({world.id})\n")

# TEST 1: Crear propuesta LIVE
print("📝 TEST 1: Propuesta LIVE")
print("-" * 60)
try:
    live_proposal = LiveProposalService.create_proposal(
        world=world,
        proposed_name=f"{world.name} - Actualizado",
        proposed_description="Descripción de prueba para propuesta LIVE",
        author=user,
        change_log="Test de propuesta LIVE"
    )
    print(f"✅ Propuesta LIVE creada:")
    print(f"   ID: {live_proposal.id}")
    print(f"   Tipo: {live_proposal.change_type}")
    print(f"   Estado: {live_proposal.status}")
    print(f"   Versión: {live_proposal.version_number}")
    print(f"   Es LIVE: {live_proposal.is_live_proposal()}")
    print(f"   Es TIMELINE: {live_proposal.is_timeline_proposal()}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# TEST 2: Crear propuesta TIMELINE
print("📅 TEST 2: Propuesta TIMELINE")
print("-" * 60)
try:
    snapshot = {
        'description': 'En el año 1500, esta entidad experimentó grandes cambios...',
        'metadata': {
            'datos_nucleo': {
                'poblacion': '10000',
                'estado': 'En desarrollo'
            }
        },
        'images': [],
        'cover_image': None
    }
    
    timeline_proposal = TimelineProposalService.create_proposal(
        world=world,
        year=1500,
        snapshot=snapshot,
        author=user,
        change_log="Test de snapshot temporal"
    )
    print(f"✅ Propuesta TIMELINE creada:")
    print(f"   ID: {timeline_proposal.id}")
    print(f"   Tipo: {timeline_proposal.change_type}")
    print(f"   Año: {timeline_proposal.timeline_year}")
    print(f"   Estado: {timeline_proposal.status}")
    print(f"   Es LIVE: {timeline_proposal.is_live_proposal()}")
    print(f"   Es TIMELINE: {timeline_proposal.is_timeline_proposal()}")
    print(f"   Snapshot keys: {list(timeline_proposal.proposed_snapshot.keys())}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# TEST 3: Listar propuestas pendientes
print("📋 TEST 3: Listar Propuestas Pendientes")
print("-" * 60)
try:
    from src.Shared.Services.ProposalService import ProposalService
    
    all_pending = ProposalService.get_pending_proposals()
    live_pending = ProposalService.get_pending_proposals(change_type='LIVE')
    timeline_pending = ProposalService.get_pending_proposals(change_type='TIMELINE')
    
    print(f"Total pendientes: {len(all_pending)}")
    print(f"LIVE pendientes: {len(live_pending)}")
    print(f"TIMELINE pendientes: {len(timeline_pending)}")
    
    if timeline_pending:
        print("\nPropuestas TIMELINE:")
        for p in timeline_pending:
            print(f"  - {p.world.name} (Año {p.timeline_year})")
    
    if live_pending:
        print("\nPropuestas LIVE:")
        for p in live_pending:
            print(f"  - {p.proposed_name} (v{p.version_number})")
    
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 60)
print("✅ Tests completados!")
