import os
import sys
import django

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src')) # Ensure src is resolvable as top-level if needed
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.Infrastructure.DjangoFramework.settings")
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import UserProfile

def setup_users():
    print("🚀 Iniciando configuración de usuarios de prueba...")

    # 1. PEPE (ADMIN)
    pepe, _ = User.objects.get_or_create(username="Pepe")
    if _: 
        pepe.set_password("pepe123")
        pepe.save()
        print("✅ Usuario 'Pepe' creado.")
    
    p_pepe, _ = UserProfile.objects.get_or_create(user=pepe)
    p_pepe.rank = 'ADMIN'
    p_pepe.save()
    print("   👑 Rango asignado: ADMIN")

    # 2. MARIA (SUBADMIN / COLLABORATOR)
    maria, _ = User.objects.get_or_create(username="Maria")
    if _: 
        maria.set_password("maria123")
        maria.save()
        print("✅ Usuario 'Maria' creado.")

    p_maria, _ = UserProfile.objects.get_or_create(user=maria)
    p_maria.rank = 'SUBADMIN'
    p_maria.save()
    print("   🛠️ Rango asignado: SUBADMIN")

    # LINK: PEPE IS BOSS OF MARIA
    p_pepe.collaborators.add(p_maria)
    p_maria.bosses.add(p_pepe)
    print("   🔗 Vinculación: Pepe es Jefe de María.")

    # 3. CURI (EXPLORER)
    curi, _ = User.objects.get_or_create(username="Curi")
    if _: 
        curi.set_password("curi123")
        curi.save()
        print("✅ Usuario 'Curi' creado.")

    p_curi, _ = UserProfile.objects.get_or_create(user=curi)
    p_curi.rank = 'EXPLORER'
    p_curi.save()
    print("   🌍 Rango asignado: EXPLORER (Solo lectura pública)")

    print("\n✨ Configuración completada. Puedes entrar con:")
    print("   - Pepe / pepe123 (Admin)")
    print("   - Maria / maria123 (SubAdmin de Pepe)")
    print("   - Curi / curi123 (Explorador)")

if __name__ == "__main__":
    setup_users()
