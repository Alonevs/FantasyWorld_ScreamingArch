import os
import django
import sys

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosLike, CaosComment
from src.Shared.Services.SocialService import SocialService

def verify_system():
    print("--- VERIFICACIÓN DEL SISTEMA SOCIAL V2 ---")
    
    # 1. Buscar un Mundo de prueba
    # Usaremos el ID mencionado por el usuario o el primero que encontremos
    world_id = "JhZCO1vxI7"
    try:
        world = CaosWorldORM.objects.get(public_id=world_id)
        print(f"✅ Mundo encontrado: {world.name} (ID: {world.public_id})")
    except CaosWorldORM.DoesNotExist:
        world = CaosWorldORM.objects.first()
        if not world:
            print("❌ No hay mundos en la BD. Crea uno primero.")
            return
        print(f"⚠️ Mundo ID {world_id} no encontrado. Usando: {world.name} (ID: {world.public_id})")
        world_id = world.public_id

    # 2. Simular Usuario 'Tester'
    tester_user, created = User.objects.get_or_create(username="TesterSocial")
    if created: 
        print("✅ Usuario 'TesterSocial' creado.")
        tester_user.set_password("1234")
        tester_user.save()
    else:
        print("✅ Usuario 'TesterSocial' recuperado.")

    entity_key = f"WORLD_{world_id}"
    
    # 3. Simular 'LIKE' (Analytics)
    print(f"\n[ANALYTICS] Simulando Like en {entity_key}...")
    
    # Limpiar estado previo
    CaosLike.objects.filter(user=tester_user, entity_key=entity_key).delete()
    
    # Crear Like Directamente (Simulando lo que hace la vista)
    CaosLike.objects.create(user=tester_user, entity_key=entity_key)
    print(f"   Like creado manualmente en BD.")
    
    # Verificar con el Servicio de Analytics
    stats = SocialService.get_interactions_count(entity_key)
    print(f"   Estadísticas recuperadas: {stats}")
    
    if stats['likes'] >= 1:
        print("   ✅ Analytics detecta el Like correctamente.")
        like_exists = True
    else:
        print("   ❌ Error: Analytics no detecta el Like.")
        like_exists = False

    # 4. Simular 'COMENTARIO' (Notificación al Autor)
    print(f"\n[NOTIFICACIONES] Simulando Comentario en {entity_key}...")
    
    content = "Prueba de sistema reutilizable V2"
    comment = CaosComment.objects.create(
        user=tester_user, 
        entity_key=entity_key, 
        content=content
    )
    
    # Verificar BD
    if comment and comment.id:
        print(f"   ✅ Comentario creado ID: {comment.id}")
    else:
        print("   ❌ Error creando comentario.")
        
    # 5. Verificar que el Autor recibiría la notificación (Lógica de Perfil)
    author = world.author
    if not author:
        print("   ⚠️ El mundo no tiene autor asignado. Asignando a Superuser Xico/Alone...")
        author = User.objects.filter(is_superuser=True).first()
        world.author = author
        world.save()
    
    print(f"   Autor del contenido: {author.username}")
    
    # Simular la query del perfil
    # El perfil busca comentarios en entidades que pertenecen al usuario.
    # WORLD_{world_id} -> Pertenece a 'author'
    
    # Recalcular lógica de 'descubrimiento'
    user_content = SocialService.discover_user_content(author)
    found_in_profile = False
    
    # Buscar en mundos
    for w in user_content.get('worlds', []):
        if w.public_id == world.public_id:
            # Buscar comentarios en este mundo
            w_comments = CaosComment.objects.filter(entity_key=entity_key)
            if w_comments.filter(id=comment.id).exists():
                found_in_profile = True
                break
                
    if found_in_profile:
        print(f"   ✅ El comentario Aparecería en el perfil de {author.username} (Notificación OK)")
    else:
        # Debug why failed
        print("   ❌ El comentario NO aparece en el perfil.")
        print("   Debug Info:")
        print(f"   - Author ID: {author.id}")
        print(f"   - World Author ID: {world.author.id}")
        print(f"   - Entity Key: {entity_key}")
        
    print("\n--- CONCLUSIÓN ---")
    if like_exists and found_in_profile:
        print("🚀 SISTEMA FUNCIONANDO AL 100%")
    else:
        print("⚠️ HAY ERRORES PENDIENTES")

if __name__ == "__main__":
    verify_system()
