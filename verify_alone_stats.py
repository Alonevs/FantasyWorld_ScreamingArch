import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Shared.Services.SocialService import SocialService

def verify_stats():
    try:
        user = User.objects.get(username='Alone')
        print(f"User: {user.username} (ID: {user.id})")
        
        content = SocialService.discover_user_content(user)
        print(f"Discovered {len(content['images'])} images, {len(content['narratives'])} narratives, {len(content['worlds'])} worlds.")
        
        comments_received = 0
        favorite_reviews = 0
        
        for img in content['images']:
            stats = SocialService.get_interactions_count(f"IMG_{img['filename']}")
            comments_received += stats['comments']
            favorite_reviews += stats['likes']
            if stats['engagement'] > 0:
                print(f"  Image: {img['filename']} (Type: {img['type']}) -> Likes: {stats['likes']}, Comments: {stats['comments']}")

        for n in content['narratives']:
            stats = SocialService.get_interactions_count(f"NARR_{n.public_id}")
            favorite_reviews += stats['likes']
            
        for w in content['worlds']:
            stats = SocialService.get_interactions_count(f"WORLD_{w.public_id}")
            favorite_reviews += stats['likes']
            
        print("-" * 30)
        print(f"FINAL STATS FOR ALONE:")
        print(f"Comments Received: {comments_received}")
        print(f"Favorite Reviews (Likes Received): {favorite_reviews}")
        
    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    verify_stats()
