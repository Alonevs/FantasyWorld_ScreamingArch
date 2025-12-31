import os
import django
import sys

# Setup Django
sys.path.append(os.path.join(os.getcwd(), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Shared.Services.SocialService import SocialService
from django.contrib.auth.models import User

def check_roberto():
    roberto = User.objects.get(id=7)
    print(f"Checking activity for {roberto.username}...")
    
    activity = SocialService.get_user_activity(roberto)
    print(f"Found {activity['comments'].count()} activity items.")
    
    for c in activity['comments']:
        info = SocialService.resolve_content_by_key(c.entity_key)
        print(f"Comment: '{c.content[:30]}...' on {c.entity_key}")
        if info:
            print(f"  -> Resolved to: {info['type']} - {info['title']} (World: {info['world'].name if info['world'] else 'None'})")
        else:
            print(f"  -> Could not resolve content info")

if __name__ == "__main__":
    check_roberto()
