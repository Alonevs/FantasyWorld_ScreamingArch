import os
import django
import sys

# Setup Django Environment
sys.path.append('c:/Users/xico0/Desktop/FantasyWorld_ScreamingArch')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosNotification
from django.utils import timezone

def create_test_notification():
    try:
        # Notify 'Xico' specifically as he is the primary user usually
        target_users = User.objects.filter(username__in=['Xico', 'Alone'])
        
        if not target_users.exists():
            target_users = User.objects.filter(is_superuser=True)

        for user in target_users:
            print(f"Creating notification for user: {user.username}")
            
            CaosNotification.objects.create(
                user=user,
                title="🔔 Prueba de Notificación",
                message=f"Esta es una notificación de prueba generada a las {timezone.now().strftime('%H:%M:%S')}.",
                url="/dashboard/"
            )
            print(f"✅ Notification created successfully for {user.username}.")
        
    except Exception as e:
        print(f"❌ Error creating notification: {e}")

if __name__ == "__main__":
    create_test_notification()
