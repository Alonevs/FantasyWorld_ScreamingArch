import os
import django
import sys

# Setup Django
sys.path.append(os.path.join(os.getcwd(), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Shared.Services.SocialService import SocialService
from django.contrib.auth.models import User

def verify_fix():
    user = User.objects.get(id=2)
    print(f"Testing discover_user_content for {user.username}...")
    
    try:
        # Test with default (True)
        content = SocialService.discover_user_content(user)
        print("Default call success.")
        
        # Test with explicit True
        content = SocialService.discover_user_content(user, include_proposals=True)
        print("Explicit True call success.")
        
        # Test with explicit False
        content = SocialService.discover_user_content(user, include_proposals=False)
        print("Explicit False call success.")
        
        print("Verification complete! No NameError found.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    verify_fix()
