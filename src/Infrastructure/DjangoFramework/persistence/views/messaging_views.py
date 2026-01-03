from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from ..models import Message

@login_required
def inbox(request):
    """Bandeja de entrada del usuario."""
    received = Message.objects.filter(recipient=request.user).order_by('-created_at')
    sent = Message.objects.filter(sender=request.user).order_by('-created_at')
    
    # Enrich with Social Hub Info
    from src.Infrastructure.DjangoFramework.persistence.models import CaosComment
    from src.Shared.Services.SocialService import SocialService
    from django.db.models import Q
    
    # 1. Get User Content Keys
    content_data = SocialService.discover_user_content(request.user)
    my_keys = []
    for w in content_data['worlds']: my_keys.extend([str(w.id), f"WORLD_{w.public_id}", w.public_id])
    for n in content_data['narratives']: my_keys.extend([n.nid, n.public_id, f"narr_{n.public_id}"])
    for img in content_data['images']: my_keys.extend([f"IMG_{img['filename']}", img['filename']])
    
    # 2. Count New Comments
    social_new_count = CaosComment.objects.filter(
        (Q(entity_key__in=my_keys) | Q(parent_comment__user=request.user))
    ).exclude(user=request.user).exclude(status='DELETED').filter(status='NEW').count()

    return render(request, 'messaging/inbox.html', {
        'received_messages': received,
        'sent_messages': sent,
        'social_new_count': social_new_count
    })

@login_required
def send_message(request, user_id=None):
    """Enviar un nuevo mensaje."""
    recipient = None
    if user_id:
        recipient = get_object_or_404(User, id=user_id)
        
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        
        target_recipient = get_object_or_404(User, id=recipient_id)
        
        Message.objects.create(
            sender=request.user,
            recipient=target_recipient,
            subject=subject,
            body=body
        )
        messages.success(request, f"Mensaje enviado con éxito a {target_recipient.username}")
        return redirect('inbox')
        
    # Para el formulario inicial
    users = User.objects.exclude(id=request.user.id).order_by('username')
    return render(request, 'messaging/compose.html', {
        'users': users,
        'initial_recipient': recipient
    })

@login_required
def mark_as_read(request, message_id):
    """Marcar un mensaje como leído."""
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    if not message.read_at:
        message.read_at = timezone.now()
        message.save()
    return JsonResponse({'status': 'ok'})

@login_required
def unread_count(request):
    """API para obtener el número de mensajes no leídos."""
    count = Message.objects.filter(recipient=request.user, read_at__isnull=True).count()
    return JsonResponse({'unread_count': count})
