from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from src.Infrastructure.DjangoFramework.persistence.models import CaosNotification

@login_required
def mark_notification_read(request, notification_id):
    """
    Marca una notificación específica como leída (visto).
    """
    notification = get_object_or_404(CaosNotification, id=notification_id, user=request.user)
    notification.read_at = timezone.now()
    notification.save()
    return JsonResponse({'status': 'ok', 'message': 'Notification marked as read'})

@login_required
def mark_all_notifications_read(request):
    """
    Marca todas las notificaciones del usuario como leídas.
    """
    CaosNotification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
    return JsonResponse({'status': 'ok', 'message': 'All notifications marked as read'})
