"""
Script para verificar permisos del usuario
"""
from django.contrib.auth.models import User

user_id = 1  # Cambiar al ID del usuario que está probando
try:
    user = User.objects.get(id=user_id)
    print(f"\n=== Usuario: {user.username} ===")
    print(f"is_superuser: {user.is_superuser}")
    print(f"is_staff: {user.is_staff}")
    
    if hasattr(user, 'profile'):
        print(f"profile.rank: {user.profile.rank}")
    else:
        print("No tiene profile")
        
    # Check condition
    is_admin = user.is_superuser or (hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUPERADMIN'])
    print(f"\n¿Debería ver Analytics?: {is_admin}")
    
except User.DoesNotExist:
    print(f"Usuario {user_id} no existe")
