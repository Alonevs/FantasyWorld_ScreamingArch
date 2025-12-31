"""
Script para verificar si hay datos de likes y comentarios en la BD
"""
from src.Infrastructure.DjangoFramework.persistence.models import CaosComment, CaosLike
from django.contrib.auth.models import User

print("\n=== VERIFICACIÓN DE DATOS ===\n")

# Total de likes y comentarios
total_likes = CaosLike.objects.count()
total_comments = CaosComment.objects.count()

print(f"Total de likes en BD: {total_likes}")
print(f"Total de comentarios en BD: {total_comments}")

# Mostrar algunos ejemplos
if total_likes > 0:
    print("\n--- Ejemplos de Likes ---")
    for like in CaosLike.objects.all()[:10]:
        print(f"  {like.user.username} → {like.entity_key}")

if total_comments > 0:
    print("\n--- Ejemplos de Comentarios ---")
    for comment in CaosComment.objects.all()[:10]:
        print(f"  {comment.user.username} en {comment.entity_key}: {comment.content[:50]}")

# Verificar usuario específico
try:
    user = User.objects.get(id=2)
    print(f"\n--- Usuario ID 2: {user.username} ---")
    
    # Comentarios del usuario
    user_comments = CaosComment.objects.filter(user=user).count()
    print(f"Comentarios escritos: {user_comments}")
    
    # Likes del usuario
    user_likes = CaosLike.objects.filter(user=user).count()
    print(f"Likes dados: {user_likes}")
    
except User.DoesNotExist:
    print("\nUsuario ID 2 no existe")

print("\n=== FIN ===\n")
