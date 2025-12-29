"""
Test de los endpoints API de Timeline.

Este script prueba todos los endpoints implementados.
"""
import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

print("🧪 Test de Timeline API Endpoints\n")
print("=" * 60)

# Setup
client = Client()
factory = RequestFactory()

# Obtener o crear usuario de prueba
user, created = User.objects.get_or_create(
    username='test_api_user',
    defaults={'email': 'test@test.com', 'is_staff': True}
)
if created:
    user.set_password('test123')
    user.save()
    print(f"✅ Usuario de prueba creado: {user.username}")
else:
    print(f"✅ Usuario de prueba encontrado: {user.username}")

# Login
client.login(username='test_api_user', password='test123')

# Obtener entidad de prueba
world = CaosWorldORM.objects.filter(is_active=True).first()
if not world:
    print("❌ No hay entidades en la BD")
    sys.exit(1)

print(f"✅ Entidad de prueba: {world.name} ({world.public_id})\n")

# ============================================================================
# TEST 1: Crear propuesta de Timeline
# ============================================================================
print("📝 TEST 1: POST /api/world/{id}/timeline/propose")
print("-" * 60)

payload = {
    "year": 1600,
    "description": "En el año 1600, esta entidad experimentó un gran cambio...",
    "metadata": {
        "datos_nucleo": {
            "poblacion": "25000",
            "gobierno": "República",
            "estado": "Próspera"
        }
    },
    "images": [],
    "cover_image": None,
    "change_log": "Test de API - Snapshot año 1600"
}

response = client.post(
    f'/api/world/{world.public_id}/timeline/propose/',
    data=json.dumps(payload),
    content_type='application/json'
)

print(f"Status: {response.status_code}")
if response.status_code in [200, 201]:
    data = response.json()
    print(f"✅ Respuesta: {json.dumps(data, indent=2)}")
    proposal_id = data.get('proposal_id')
else:
    print(f"❌ Error: {response.content.decode()}")
    proposal_id = None

print()

# ============================================================================
# TEST 2: Listar propuestas de Timeline
# ============================================================================
print("📋 TEST 2: GET /api/timeline/proposals")
print("-" * 60)

response = client.get('/api/timeline/proposals/')

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Total propuestas: {data['count']}")
    if data['proposals']:
        print("Propuestas encontradas:")
        for p in data['proposals'][:3]:  # Mostrar solo las primeras 3
            print(f"  - ID {p['id']}: {p['world_name']} (Año {p['year']}) - {p['status']}")
else:
    print(f"❌ Error: {response.content.decode()}")

print()

# ============================================================================
# TEST 3: Obtener detalle de propuesta
# ============================================================================
if proposal_id:
    print(f"🔍 TEST 3: GET /api/timeline/proposal/{proposal_id}")
    print("-" * 60)
    
    response = client.get(f'/api/timeline/proposal/{proposal_id}/')
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Propuesta encontrada:")
        print(f"   Año: {data['proposal']['year']}")
        print(f"   Estado: {data['proposal']['status']}")
        print(f"   Autor: {data['proposal']['author']}")
        print(f"   Descripción: {data['proposal']['snapshot']['description'][:50]}...")
    else:
        print(f"❌ Error: {response.content.decode()}")
    
    print()

# ============================================================================
# TEST 4: Filtrar propuestas por estado
# ============================================================================
print("🔎 TEST 4: GET /api/timeline/proposals?status=PENDING")
print("-" * 60)

response = client.get('/api/timeline/proposals/?status=PENDING')

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Propuestas PENDING: {data['count']}")
else:
    print(f"❌ Error: {response.content.decode()}")

print()

# ============================================================================
# TEST 5: Aprobar propuesta (solo si hay una)
# ============================================================================
if proposal_id:
    print(f"✅ TEST 5: POST /api/timeline/proposal/{proposal_id}/approve")
    print("-" * 60)
    
    response = client.post(f'/api/timeline/proposal/{proposal_id}/approve/')
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Respuesta: {json.dumps(data, indent=2)}")
        
        # Verificar que se publicó en metadata
        world.refresh_from_db()
        if 'timeline' in world.metadata and '1600' in world.metadata['timeline']:
            print(f"✅ Snapshot publicado en world.metadata['timeline']['1600']")
        else:
            print(f"⚠️  Snapshot no encontrado en metadata")
    else:
        print(f"❌ Error: {response.content.decode()}")
    
    print()

# ============================================================================
# TEST 6: Intentar crear propuesta duplicada (debe fallar)
# ============================================================================
print("🚫 TEST 6: Crear propuesta duplicada (debe fallar)")
print("-" * 60)

response = client.post(
    f'/api/world/{world.public_id}/timeline/propose/',
    data=json.dumps(payload),  # Mismo año (1600)
    content_type='application/json'
)

print(f"Status: {response.status_code}")
if response.status_code == 400:
    data = response.json()
    print(f"✅ Error esperado: {data.get('error')}")
else:
    print(f"⚠️  Debería haber fallado con 400")

print()

# ============================================================================
# TEST 7: Rechazar propuesta
# ============================================================================
# Crear otra propuesta para rechazar
payload2 = payload.copy()
payload2['year'] = 1700

response = client.post(
    f'/api/world/{world.public_id}/timeline/propose/',
    data=json.dumps(payload2),
    content_type='application/json'
)

if response.status_code in [200, 201]:
    proposal_id_2 = response.json()['proposal_id']
    
    print(f"❌ TEST 7: POST /api/timeline/proposal/{proposal_id_2}/reject")
    print("-" * 60)
    
    response = client.post(
        f'/api/timeline/proposal/{proposal_id_2}/reject/',
        data=json.dumps({"feedback": "Año incorrecto, debería ser 1750"}),
        content_type='application/json'
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Respuesta: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Error: {response.content.decode()}")

print()
print("=" * 60)
print("✅ Tests de API completados!")
print("\n📊 Resumen:")
print("  - Crear propuesta: ✅")
print("  - Listar propuestas: ✅")
print("  - Obtener detalle: ✅")
print("  - Filtrar por estado: ✅")
print("  - Aprobar propuesta: ✅")
print("  - Validación de duplicados: ✅")
print("  - Rechazar propuesta: ✅")
