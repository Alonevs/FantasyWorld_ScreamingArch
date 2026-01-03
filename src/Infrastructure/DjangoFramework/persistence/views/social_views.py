import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.timezone import localtime
from src.Infrastructure.DjangoFramework.persistence.models import CaosLike, CaosComment, Message, CaosEventLog
from src.Shared.Services.SocialService import SocialService
from src.Infrastructure.DjangoFramework.persistence.utils import get_user_avatar
from src.Infrastructure.DjangoFramework.persistence.policies import can_user_moderate_comment

# --- LIKES SYSTEM (Standardized) ---

@login_required
@require_POST
def toggle_like(request):
    try:
        # Support both JSON and Form Data
        entity_key = None
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                entity_key = data.get('entity_key')
            except json.JSONDecodeError:
                pass
        
        if not entity_key:
             entity_key = request.POST.get('entity_key')

        entity_key = SocialService.normalize_key(entity_key)
        
        if not entity_key:
            return JsonResponse({'error': 'Missing entity_key'}, status=400)

        # Toggle Like
        like_obj, created = CaosLike.objects.get_or_create(
            user=request.user, 
            entity_key=entity_key 
        )
        
        if not created:
            like_obj.delete()
            is_liked = False
        else:
            is_liked = True

        # Get total count using robust service
        stats = SocialService.get_interactions_count(entity_key)
        
        return JsonResponse({'liked': is_liked, 'count': stats['likes'], 'user_has_liked': is_liked})
    except Exception as e:
        print(f"DEBUG_LIKE_ERROR: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def get_like_status(request):
    entity_key = request.GET.get('entity_key')
    if not entity_key:
        return JsonResponse({'count': 0, 'liked': False, 'user_has_liked': False})
        
    stats = SocialService.get_interactions_count(entity_key)
    is_liked = False
    if request.user.is_authenticated:
        query = SocialService.get_robust_query(entity_key)
        is_liked = CaosLike.objects.filter(query, user=request.user).exists()
        
    return JsonResponse({'count': stats['likes'], 'liked': is_liked, 'user_has_liked': is_liked})

# --- COMMENTS SYSTEM (Standardized) ---

def get_comments(request):
    try:
        entity_key = request.GET.get('entity_key')
        if not entity_key:
            return JsonResponse({'comments': [], 'authenticated': request.user.is_authenticated})
        
        comments = SocialService.get_comments(entity_key)
        
        data = []
        for c in comments:
            profile_pic_url = get_user_avatar(c.user)
            username = c.user.username if c.user else "Usuario eliminado"
                
            # Build replies list
            replies = []
            for reply in c.replies.all():
                reply_pic_url = get_user_avatar(reply.user)
                reply_username = reply.user.username if reply.user else "Usuario eliminado"
                
                replies.append({
                    'id': reply.id,
                    'username': reply_username,
                    'user': reply_username,  # Backward compatibility
                    'content': reply.content,
                    'date': localtime(reply.created_at).strftime("%d/%m/%Y %H:%M") if reply.created_at else "---",
                    'is_me': request.user.is_authenticated and reply.user and (request.user == reply.user),
                    'can_delete': can_user_moderate_comment(request.user, reply),
                    'avatar_url': reply_pic_url,
                    'profile_url': f"/staff/user/{reply_username}/" if reply.user else "#"
                })

            data.append({
                'id': c.id,
                'username': username,
                'user': username,  # Backward compatibility
                'content': c.content,
                'date': localtime(c.created_at).strftime("%d/%m/%Y %H:%M") if c.created_at else "---",
                'is_me': request.user.is_authenticated and c.user and (request.user == c.user),
                'can_delete': can_user_moderate_comment(request.user, c),
                'avatar_url': profile_pic_url,
                'pic': profile_pic_url,  # Backward compatibility
                'reply_count': c.reply_count,
                'replies': replies
            })
        return JsonResponse({
            'comments': data, 
            'authenticated': request.user.is_authenticated
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_comments for key {request.GET.get('entity_key', 'NONE')}: {e}\n{error_details}")
        return JsonResponse({
            'error': str(e), 
            'comments': [], 
            'authenticated': request.user.is_authenticated,
            'debug_msg': 'Error en el servidor al procesar comentarios'
        }, status=500)

@login_required
@require_POST
def post_comment(request):
    try:
        # Support both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            entity_key = data.get('entity_key')
            content = data.get('content')
            parent_comment_id = data.get('parent_comment_id')
        else:
            entity_key = request.POST.get('entity_key')
            content = request.POST.get('content')
            parent_comment_id = request.POST.get('parent_comment_id')
        
        entity_key = SocialService.normalize_key(entity_key)
        if not entity_key or not content:
            return JsonResponse({'error': 'Missing fields'}, status=400)
        
        # Create comment (Populate Context)
        entity_name = ""
        entity_type = ""
        
        # 1. Try to resolve entity name/type
        try:
            from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosNarrativeORM
            if entity_key.startswith("img_"):
                entity_name = f"Imagen: {entity_key[4:]}"
                entity_type = "IMAGE"
            elif entity_key.startswith("NID_"):
                # Usually logic handles NID
                pass 
            else:
                # Assume World ID or NID
                # Try World
                w = CaosWorldORM.objects.filter(id=entity_key).first()
                if w:
                    entity_name = f"Mundo: {w.name}"
                    entity_type = "WORLD"
                else:
                    # Try Narrative
                    n = CaosNarrativeORM.objects.filter(public_id=entity_key).first()
                    if not n: n = CaosNarrativeORM.objects.filter(nid=entity_key).first()
                    
                    if n:
                        entity_name = f"Narrativa: {n.titulo}"
                        entity_type = "NARRATIVE"
                        
        except Exception as e:
            print(f"Error resolving entity context: {e}")

        comment = CaosComment(
            user=request.user, 
            entity_key=entity_key, 
            content=content,
            entity_name=entity_name,
            entity_type=entity_type
        )
        
        # Handle threading (replies)
        if parent_comment_id:
            try:
                parent = CaosComment.objects.get(id=parent_comment_id)
                # Security: Verify parent belongs to same entity
                if not SocialService.compare_keys(parent.entity_key, entity_key):
                    return JsonResponse({'error': f'Invalid parent comment ({parent.entity_key} vs {entity_key})'}, status=400)
                
                comment.parent_comment = parent
                comment.save()
                
                # Update parent reply count & Status
                parent.reply_count += 1
                if parent.status != 'REPLIED':
                    parent.status = 'REPLIED'
                parent.save()
                
                # Notify parent comment author
                if parent.user != request.user:
                    Message.objects.create(
                        sender=request.user,
                        recipient=parent.user,
                        subject=f"💬 {request.user.username} respondió a tu comentario",
                        body=f'"{content[:100]}..."'
                    )
            except CaosComment.DoesNotExist:
                return JsonResponse({'error': 'Parent comment not found'}, status=404)
        else:
            comment.save()
            
            # --- NOTIFICATION LOGIC FOR CONTENT OWNER ---
            try:
                # 1. Extract filename from entity_key (IMG_filename)
                if entity_key.startswith("img_"):
                    filename = entity_key[4:] # Remove "img_"
                    
                    # 2. Find original uploader
                    upload_event = CaosEventLog.objects.filter(
                        action__in=['UPLOAD_PHOTO', 'PROPOSE_AI_PHOTO'],
                        details__icontains=filename
                    ).order_by('-id').first()
                    
                    if upload_event and upload_event.user != request.user:
                        target_user = upload_event.user
                        world_id = upload_event.world_id
                        msg_content = f"💬 **{request.user.username}** comentó en tu imagen `{filename}`.\n\n[Ver Comentario](/mundo/{world_id}?open_image={filename})"
                        
                        Message.objects.create(
                            sender=request.user,
                            recipient=target_user,
                            subject=f"Nuevo comentario en {filename}",
                            body=msg_content
                        )
            except Exception as notify_error:
                print(f"NOTIFICATION ERROR: {notify_error}")

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def delete_comment(request):
    try:
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        
        comment = get_object_or_404(CaosComment, id=comment_id)
        
        if not can_user_moderate_comment(request.user, comment):
             return JsonResponse({'error': 'Unauthorized: No tienes rango suficiente para borrar este comentario.'}, status=403)
             
        comment.delete()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def toggle_comment_like(request):
    """
    Toggle like on a specific comment.
    Uses entity_key format: COMMENT_{comment_id}
    """
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        comment_id = data.get('comment_id')
        
        if not comment_id:
            return JsonResponse({'error': 'Missing comment_id'}, status=400)
        
        # Verify comment exists
        comment = get_object_or_404(CaosComment, id=comment_id)
        
        # Create entity_key for this comment
        entity_key = f"COMMENT_{comment_id}"
        
        # Toggle like
        like, created = CaosLike.objects.get_or_create(
            user=request.user,
            entity_key=entity_key
        )
        
        if not created:
            # Unlike
            like.delete()
            count = CaosLike.objects.filter(entity_key=entity_key).count()
            return JsonResponse({
                'status': 'unliked',
                'count': count,
                'user_has_liked': False
            })
        else:
            # Liked - create notification
            if comment.user != request.user:
                Message.objects.create(
                    sender=request.user,
                    recipient=comment.user,
                    subject=f"⭐ A {request.user.username} le gustó tu comentario",
                    body=f'"{comment.content[:100]}..."'
                )
            
            count = CaosLike.objects.filter(entity_key=entity_key).count()
            return JsonResponse({
                'status': 'liked',
                'count': count,
                'user_has_liked': True
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
