from src.Infrastructure.DjangoFramework.persistence.models import CaosComment, CaosLike, CaosWorldORM
from django.contrib.auth.models import User

# Get usuario2
try:
    u = User.objects.get(username='usuario2')
    print(f"\n=== USUARIO: {u.username} ===\n")
    
    # Check comments by user
    user_comments = CaosComment.objects.filter(user=u)
    print(f"Total comments by user: {user_comments.count()}")
    
    # Check likes on those comments
    total_likes = 0
    for comment in user_comments:
        entity_key = f"COMMENT_{comment.id}"
        likes_count = CaosLike.objects.filter(entity_key__iexact=entity_key).count()
        if likes_count > 0:
            print(f"  Comment {comment.id}: {likes_count} likes")
        total_likes += likes_count
    
    print(f"\nTotal RESEÑAS FAVORITAS: {total_likes}\n")
    
    # Check comments received on user's images
    comments_received = 0
    worlds = CaosWorldORM.objects.filter(author=u, is_active=True)
    print(f"User worlds: {worlds.count()}")
    
    for world in worlds:
        if world.metadata and 'gallery_log' in world.metadata:
            gallery_log = world.metadata['gallery_log']
            for filename, meta in gallery_log.items():
                if meta.get('uploader') == u.username:
                    entity_key = f"IMG_{filename}"
                    count = CaosComment.objects.filter(entity_key__iexact=entity_key).count()
                    if count > 0:
                        print(f"  {filename}: {count} comments")
                    comments_received += count
    
    print(f"\nTotal COMENTARIOS RECIBIDOS: {comments_received}\n")
    
    # Check all entity_keys in database
    print("\n=== ALL LIKES IN DATABASE ===")
    all_likes = CaosLike.objects.all()[:20]
    for like in all_likes:
        print(f"  {like.entity_key} by {like.user.username}")
    
    print("\n=== ALL COMMENTS IN DATABASE ===")
    all_comments = CaosComment.objects.all()[:20]
    for comment in all_comments:
        print(f"  {comment.entity_key} by {comment.user.username}: {comment.content[:50]}")
        
except User.DoesNotExist:
    print("Usuario 'usuario2' no existe")
