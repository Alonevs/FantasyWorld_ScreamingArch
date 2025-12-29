import os
import django
import sys

# Setup Django
sys.path.append(os.path.join(os.getcwd(), 'src', 'Infrastructure', 'DjangoFramework'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import (
    TimelinePeriod, TimelinePeriodVersion, CaosWorldORM
)
from src.Shared.Services.TimelinePeriodService import TimelinePeriodService
from django.contrib.auth.models import User

def run_test():
    print("--- INICIANDO TEST DE UNIFICACIÓN DEL DASHBOARD ---")
    
    # 1. Setup Data
    world = CaosWorldORM.objects.first()
    admin = User.objects.filter(is_superuser=True).first()
    if not world or not admin:
        print("ERROR: No hay mundos o admins para probar.")
        return

    # 2. Create a period
    period = TimelinePeriodService.create_period(
        world=world,
        title="Periodo de Test Unificacion",
        description="Para probar el dashboard",
        author=admin
    )
    print(f"Creado periodo: {period.title}")
    
    # 3. Propose a deletion
    version = TimelinePeriodService.propose_delete(
        period=period,
        author=admin,
        reason="Test de borrado unificado"
    )
    print(f"Propuesta de borrado creada. Action: {version.action}, Status: {version.status}")
    
    # Verify metadata unification
    print(f"Metadata en la propuesta: {version.proposed_metadata}")

    # 4. Approve the deletion
    TimelinePeriodService.approve_version(version, admin)
    print("Propuesta aprobada.")
    
    # 5. Verify physical/logical deletion
    exists = TimelinePeriod.objects.filter(id=period.id).exists()
    if not exists:
        print("✅ ÉXITO: El periodo ha sido eliminado tras aprobar la propuesta de borrado.")
    else:
        print("❌ FALLO: El periodo sigue existiendo.")

    # 6. Test ADD proposal (implicit in create_period)
    print("--- TEST FINALIZADO ---")

if __name__ == "__main__":
    run_test()
