import os
import sys
import django
from django.utils.text import slugify

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, 
    TimelinePeriod, 
    TimelinePeriodVersion
)
from src.Shared.Services.TimelinePeriodService import TimelinePeriodService
from django.contrib.auth.models import User

def test_timeline_crud():
    print("--- Iniciando Pruebas del Sistema de Timeline ---")
    
    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    world = CaosWorldORM.objects.filter(is_active=True).first()
    
    if not world:
        print("Error: No se encontro ninguna entidad para probar.")
        return

    print(f"Probando con entidad: {world.name} ({world.public_id})")

    # 1. Prueba de CREACION
    print("\n1. Probando Creacion...")
    title = "Era de Pruebas"
    desc = "Una era para testear el sistema."
    
    # Limpiar si existe
    TimelinePeriod.objects.filter(world=world, title=title).delete()
    
    period = TimelinePeriodService.create_period(
        world=world,
        title=title,
        description=desc,
        author=admin_user
    )
    
    assert period.title == title
    assert period.description == desc
    assert period.versions.count() == 1
    assert period.versions.first().status == 'APPROVED'
    print("  [OK] Creacion exitosa.")

    # 2. Prueba de PROPUESTA DE EDICION
    print("\n2. Probando Propuesta de Edicion...")
    new_title = "Era de Pruebas (Editada)"
    new_desc = "Descripcion modificada."
    
    proposal = TimelinePeriodService.propose_edit(
        period=period,
        title=new_title,
        description=new_desc,
        author=admin_user,
        change_log="Cambio de prueba"
    )
    
    assert proposal.status == 'PENDING'
    assert proposal.proposed_title == new_title
    assert proposal.proposed_description == new_desc
    # El periodo original no debe haber cambiado todavia
    period.refresh_from_db()
    assert period.title == title 
    print("  [OK] Propuesta de edicion creada como PENDING.")

    # 3. Prueba de APROBACION
    print("\n3. Probando Aprobacion...")
    TimelinePeriodService.approve_version(proposal, admin_user)
    
    period.refresh_from_db()
    assert period.title == new_title
    assert period.description == new_desc
    assert proposal.status == 'APPROVED'
    print("  [OK] Aprobacion aplicada correctamente al periodo.")

    # 4. Prueba de ELIMINACION (No ACTUAL)
    print("\n4. Probando Eliminacion...")
    period_id = period.id
    TimelinePeriodService.delete_period(period)
    assert not TimelinePeriod.objects.filter(id=period_id).exists()
    print("  [OK] Eliminacion de periodo historico exitosa.")

    # 5. Prueba de SEGURIDAD (No borrar ACTUAL)
    print("\n5. Probando Proteccion de ACTUAL...")
    actual_period = TimelinePeriodService.get_current_period(world)
    try:
        TimelinePeriodService.delete_period(actual_period)
        print("  [FAIL] Se permitio borrar el periodo ACTUAL!")
    except ValueError as e:
        print(f"  [OK] Bloqueo correcto: {e}")

    print("\n--- ¡Todas las pruebas pasaron con exito! ---")

if __name__ == "__main__":
    try:
        test_timeline_crud()
    except AssertionError as e:
        print(f"\n[ERROR] Fallo en la verificacion: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
