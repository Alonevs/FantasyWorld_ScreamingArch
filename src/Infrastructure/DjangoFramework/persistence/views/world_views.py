import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.timezone import localtime

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosNarrativeORM, CaosEventLog, MetadataTemplate, TimelinePeriodVersion, CaosLike, UserProfile, CaosComment, Message
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from django.db.models import Q, Case, When, Value, IntegerField, Count
import json
from django.http import JsonResponse
from src.Shared.Services.SocialService import SocialService

# --- LIKES SYSTEM (Simple) ---
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
        
        print(f"DEBUG_LIKE: Toggle request from {request.user} for {entity_key}")

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

# --- COMMENTS SYSTEM (Simple) ---
def get_comments(request):
    try:
        entity_key = request.GET.get('entity_key')
        if not entity_key:
            return JsonResponse({'comments': [], 'authenticated': request.user.is_authenticated})
        
        comments = SocialService.get_comments(entity_key)
        
        from src.Infrastructure.DjangoFramework.persistence.utils import get_user_avatar
        from src.Infrastructure.DjangoFramework.persistence.policies import can_user_moderate_comment
        
        data = []
        for c in comments:
            # Use centralized avatar logic
            profile_pic_url = get_user_avatar(c.user)
            username = c.user.username if c.user else "Usuario eliminado"
                
            # Build replies list
            replies = []
            for reply in c.replies.all():
                # Use centralized avatar logic for replies too
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
        
        # Create comment
        comment = CaosComment(user=request.user, entity_key=entity_key, content=content)
        
        # Handle threading (replies)
        if parent_comment_id:
            try:
                parent = CaosComment.objects.get(id=parent_comment_id)
                # Security: Verify parent belongs to same entity
                if not SocialService.compare_keys(parent.entity_key, entity_key):
                    return JsonResponse({'error': f'Invalid parent comment ({parent.entity_key} vs {entity_key})'}, status=400)
                
                comment.parent_comment = parent
                comment.save()
                
                # Update parent reply count
                parent.reply_count += 1
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
                        # 3. Send Notification
                        target_user = upload_event.user
                        
                        # Construct Deep Link
                        # /mundo/<public_id>?open_image=<filename>
                        # We need the world public_id. The event has 'world_id' (which is the public_id usually in event logs or we can derive it)
                        # Actually CaosEventLog stores world_id as the ID, not public_id necessarily. 
                        # Let's check how CaosEventLog stores world_id. usually it is the public_id string if we follow log_event usage.
                        # But if not, we can try to resolve it. OR the frontend might already know it.
                        # For safety, let's assume world_id in details or we assume the current world context. 
                        # WAIT: The comment doesn't know the world ID. 
                        # However, the filename is unique per world folder... usually.
                        # Let's try to get the world from the event log if possible.
                        
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
        
        # Check Permissions using centralized policy
        from src.Infrastructure.DjangoFramework.persistence.policies import can_user_moderate_comment
        
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

@login_required
@require_POST
def update_avatar(request):
    try:
        if 'avatar' not in request.FILES:
            return JsonResponse({'error': 'No image provided'}, status=400)
            
        file = request.FILES['avatar']
        
        # Ensure Profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Save
        profile.avatar = file
        profile.save()
        
        return JsonResponse({'status': 'ok', 'url': profile.avatar.url})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# -----------------------------
from django.http import Http404
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.generate_creature_usecase import GenerateCreatureUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
from django.contrib.auth.decorators import login_required, user_passes_test
from src.FantasyWorld.Domain.Services.EntityService import EntityService
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Application.toggle_visibility import ToggleWorldVisibilityUseCase
from src.WorldManagement.Caos.Application.toggle_lock import ToggleWorldLockUseCase
from src.WorldManagement.Caos.Application.get_world_tree import GetWorldTreeUseCase
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs, get_world_images
from .view_utils import resolve_jid_orm, check_world_access, get_admin_status, get_metadata_diff


from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy

def log_event(user, action, target_id, details=""):
    """
    Registra eventos de auditoría en la base de datos (CaosEventLog).
    Sirve para rastrear quién hizo qué y sobre qué entidad.
    """
    try:
        u = user if user.is_authenticated else None
        CaosEventLog.objects.create(user=u, action=action, target_id=target_id, details=details)
    except Exception as e: 
        print(f"Error al registrar evento: {e}")

def get_current_user(request):
    if request.user.is_authenticated: return request.user
    u, _ = User.objects.get_or_create(username='Admin')
    return u

# Se eliminó resolve_jid local, usando resolve_jid_orm en su lugar
from django.db.models.functions import Length

def home(request):
    """
    Vista de Inicio: El Portal Central del Universo.
    Muestra el índice de mundos habitables aplicando la 'Indexación Agresiva'.
    Filtra entidades fantasma, borradores ocultos y aplica visibilidad por roles (Soberanía).
    """
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        repo = DjangoCaosRepository()
        # Para la creación, el autor es el usuario actual
        try:
            jid = CreateWorldUseCase(repo).execute(
                name=request.POST.get('world_name'), 
                description=request.POST.get('world_desc'),
                author=request.user
            )
            w = CaosWorldORM.objects.get(id=jid)
            w.author = request.user
            w.save()
            messages.success(request, "✨ Mundo propuesto. Ve al Dashboard para aprobarlo.")
        except Exception as e:
            messages.error(request, f"Error al proponer mundo: {str(e)}")
            
        return redirect('dashboard')
    
    # Mostrar mundos 'LIVE' (y 'DRAFTS' para el Autor/Superusuario)
    # 1. Base: Excluir borrados, inválidos y DRAFTS (Flujo Estricto)
    # 1. Base: Excluir solo lo que está en la papelera (soft-delete)
    # El resto de estados (DRAFT, OFFLINE) se filtran por permisos más abajo.
    ms = CaosWorldORM.objects.filter(is_active=True).exclude(status='DELETED')
    
    # Exclusión de descripciones vacías, EXCEPTO para Caos Prime (JhZCO1vxI7)
    ms = ms.exclude(
        Q(description__isnull=True) | Q(description__exact='') | Q(description__iexact='None'),
        ~Q(public_id='JhZCO1vxI7')
    )
    
    ms = ms.exclude(id__endswith='00', name__startswith='Nexo Fantasma') \
        .exclude(id__endswith='00', name__startswith='Ghost')
    
    # Regla Especial (01XX): Ocultar hijos directos de Caos Prime para no-Admins en el Home
    is_privileged = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rank == 'ADMIN')
    if not is_privileged:
        ms = ms.exclude(id__regex=r'^01[0-9]{2}$')

    ms = ms.prefetch_related('versiones', 'narrativas') \
        .order_by(
            Case(
                When(public_id='JhZCO1vxI7', then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            'name'  # Secondary sort by name
        )

    # 2. Lógica de Visibilidad Centralizada
    from src.Infrastructure.DjangoFramework.persistence.policies import get_visibility_q_filter
    
    q_filter = get_visibility_q_filter(request.user)
    ms = ms.filter(q_filter)

    # LÓGICA REPRESENTATIVA:
    # Objetivo: Ocultar "Fantasmas" (Versiones) pero MOSTRAR "Hermanos".
    # Un Fantasma se define por tener '00' en su linaje (ej. 01010001 es un fantasma de 010101).
    # Los Hermanos reales (010101, 010102) NO deben agruparse.
    

    # --- LÓGICA DE ÍNDICE DE INICIO REFRACTORIZADA ---
    # Caso de Uso: GetHomeIndexUseCase
    # Maneja: Limpieza de fantasmas, colapso de versiones e indexación agresiva para Geografía/Población.
    
    from src.WorldManagement.Caos.Application.get_home_index import GetHomeIndexUseCase
    use_case = GetHomeIndexUseCase()
    final_list = use_case.execute(ms)

    l = []
    background_images = []
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_plural_label

    for m in final_list:
        # Pasar world_instance=m para evitar re-consultar metadatos (N+1 fix)
        imgs = get_world_images(m.id, world_instance=m)
        if imgs:
            imgs.sort(key=lambda x: x.get('is_cover', False), reverse=True)
        cover = imgs[0]['url'] if imgs else None
        if m.metadata and 'cover_image' in m.metadata:
            target = m.metadata['cover_image']
            found = next((i for i in imgs if i['filename'] == target), None)
            if found: cover = found['url']
        
        if cover:
            background_images.append(cover)
 
        # Recolectar hasta 5 imágenes para el slideshow (Priorizando PORTADA)
        entity_images = [i['url'] for i in imgs] if imgs else []
        if cover and cover in entity_images:
            entity_images.remove(cover)
            entity_images.insert(0, cover)
        entity_images = entity_images[:5]
        
        # SOBRESCRITURA VISUAL DE NOMBRE (Solicitado: "solo visual")
        # Si es Nivel 1 (id="01..."), mostrar "CAOS". Nivel 2 -> "ABISMOS", etc.
        visual_name = get_plural_label(len(m.id)//2, m.id)
        # Manejar singularización o sobrescrituras específicas si es necesario
        if len(m.id)//2 == 1: visual_name = "CAOS"

        pid = m.public_id if m.public_id else m.id
        l.append({
            'id': m.id, 
            'public_id': pid, 
            'name': visual_name, 
            'real_name': m.name, # Mantener original para tooltips o alt
            'status': m.status, 
            'img_file': cover,
            'img': cover, # Fallback/Primary key
            'images': entity_images, 
            'has_img': bool(cover), 
            'visible': m.visible_publico,
            'is_locked': m.status == 'LOCKED',
            'author': m.author,
            'level': len(m.id)//2,
        })
    
    import random
    random.shuffle(background_images)
    
    return render(request, 'index.html', {'mundos': l, 'background_images': background_images[:10]})


def ver_mundo(request, public_id):
    """
    Ficha de Entidad: Muestra el Lore, Metadatos Estructurados y Galería.
    Permite la creación de entidades hijas ('Sugerencia de Creación') 
    y gestiona la normalización de metadatos para el frontend.
    """
    w_orm = resolve_jid_orm(public_id)
    if not w_orm:
        return render(request, '404.html', {"jid": public_id}, status=404)
    
    can_access, is_author_or_team = check_world_access(request, w_orm)
    if not can_access:
        return render(request, 'private_access.html', status=403)
    
    repo = DjangoCaosRepository()
    
    # 1. Manejar POST (Creación)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        # Resolver ID para el padre (necesario para la creación)
        w = resolve_jid_orm(public_id)
        if not w: return redirect('home') # Debería manejarse mejor
        
        # --- CHEQUEO DE SEGURIDAD ---
        # Permitir propuestas de cualquier usuario autenticado (Estado será PENDING)
        # Eliminamos el check_ownership() estricto aquí para habilitar el flujo de "Sugerencia/Propuesta".
        # ----------------------------

        jid = w.id
        safe_pid = w.public_id if w.public_id else jid

        c_name = request.POST.get('child_name')
        if c_name:
            c_desc = request.POST.get('child_desc', "")
            reason = request.POST.get('reason', "Creación vía Wizard")
            use_ai = request.POST.get('use_ai_gen') == 'on'
            
            target_level_str = request.POST.get('target_level')
            target_level = int(target_level_str) if target_level_str else None
            
            # Usar EntityService para creación unificada
            service = EntityService()
            new_id = service.create_entity(
                parent_id=jid, 
                name=c_name, 
                description=c_desc, 
                reason=reason, 
                generate_image=use_ai, 
                target_level=target_level,
                user=request.user
            )
            
            try:
                if target_level and target_level > (len(jid)//2 + 1):
                     messages.success(request, f"✨ Entidad profunda creada con Salto (Nivel {target_level}).")
                else:
                     messages.success(request, "✨ Entorno propuesto (y su imagen). Ve al Dashboard para aprobarlo.")
                return redirect('dashboard')
            except:
                return redirect('dashboard')

    # --- PERIOD SUPPORT (New Timeline System) ---
    from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriod
    from src.Shared.Services.TimelinePeriodService import TimelinePeriodService
    
    # Resolver Entidad ORM para el servicio de períodos
    w_orm = resolve_jid_orm(public_id)
    if not w_orm: raise Http404

    # Obtener slug del período solicitado (por defecto: 'actual')
    period_slug = request.GET.get('period', 'actual')
    
    # Obtener todos los períodos de esta entidad
    all_periods = TimelinePeriodService.get_periods_for_world(w_orm)
    
    # Obtener el período actual (ACTUAL)
    current_period = TimelinePeriodService.get_current_period(w_orm)
    
    # Determinar qué período mostrar
    if period_slug == 'actual' or not period_slug:
        viewing_period = current_period
    else:
        viewing_period = all_periods.filter(slug=period_slug).first()
        if not viewing_period:
            # Si el slug no existe, redirigir a ACTUAL
            messages.warning(request, f"Período '{period_slug}' no encontrado. Mostrando ACTUAL.")
            return redirect('ver_mundo', public_id=public_id)

    # 1.5. Check for Retouch Proposal (Period or Metadata)
    retouch_proposal = None
    prop_id = request.GET.get('proposal_id')
    if prop_id:
        # Try Period Version first
        try:
            retouch_proposal = TimelinePeriodVersion.objects.get(id=prop_id)
            messages.info(request, f"✏️ Retomando propuesta rechazada de Periodo v{retouch_proposal.version_number}. Datos cargados.")
        except TimelinePeriodVersion.DoesNotExist:
            # Try World Version
            try:
                retouch_proposal = CaosVersionORM.objects.get(id=prop_id)
                messages.info(request, f"✏️ Retomando propuesta rechazada de Mundo v{retouch_proposal.version_number}. Datos cargados.")
            except CaosVersionORM.DoesNotExist:
                pass

    # 2. Manejar GET (Visualización) mediante Caso de Uso
    # PASAMOS EL PERIOD_SLUG PARA FILTRAR IMÁGENES
    context = GetWorldDetailsUseCase(repo).execute(public_id, request.user, period_slug=period_slug)
    
    if not context:
        return render(request, '404.html', {"jid": public_id})

    # --- CANONICALIZACIÓN DE URL (ID Antiguo -> NanoID) ---
    if context['public_id'] and context['public_id'] != public_id:
        return redirect('ver_mundo', public_id=context['public_id'])
    # ------------------------------------------------------

    # Si estamos viendo un período que NO es ACTUAL, sobrescribir descripción
    if viewing_period and not viewing_period.is_current:
        context['description'] = viewing_period.description
        context['is_period_view'] = True
        context['viewing_period'] = viewing_period
        
        # Sobrescribir metadatos para mostrar los del periodo
        # Sobrescribir metadatos para mostrar los del periodo
        from .view_utils import get_metadata_properties_dict
        # Asegurar que siempre se procesen los metadatos (aunque sea dict vacío)
        props = get_metadata_properties_dict(viewing_period.metadata if viewing_period.metadata else {})
        context['props'] = props
        
        # FIX: Adaptar formato para _metadata_viewer.html (espera 'metadata_obj.properties')
        context['metadata_obj'] = {
            'properties': [{'key': k, 'value': v} for k, v in props.items()]
        }
        
    # Override Info Sidebar
        context['created_at'] = viewing_period.created_at
        context['version_live'] = viewing_period.current_version_number
        
        # Entity key for period-specific social interactions
        context['period_entity_key'] = f"period_{period_slug}_{public_id}"
        
        # Derivar Autor desde la primera versión del período
        first_v = viewing_period.versions.order_by('version_number').first()
        if first_v and first_v.author:
             context['author_live'] = first_v.author.username
             context['author_live_user'] = first_v.author
             context['author_name'] = first_v.author.username
             # Get avatar using centralized utility
             from src.Infrastructure.DjangoFramework.persistence.utils import get_user_avatar
             context['author_avatar_url'] = get_user_avatar(first_v.author, context['jid'])
        else:
             context['author_live'] = "Desconocido"
             context['author_name'] = "Desconocido"
             context['author_avatar_url'] = ""

    else:
        context['is_period_view'] = False
        context['viewing_period'] = current_period
        # Entity key for current period (uses world_ format)
        context['period_entity_key'] = f"world_{public_id}"
    
    # Pasar períodos al contexto para el selector
    context['timeline_periods'] = all_periods.exclude(is_current=True).order_by('order')
    context['current_period_slug'] = period_slug
    context['retouch_proposal'] = retouch_proposal # Pass the object or dict
    # ---------------------------------

    # --- INYECCIÓN DE ETIQUETA DE JERARQUÍA ---
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy, get_children_label # Importar helpers
    context['hierarchy_label'] = get_readable_hierarchy(context['jid'])
    context['children_label'] = get_children_label(context['jid']) # NUEVO: Pasar etiqueta para el grid
    context['status_str'] = w_orm.status
    context['author_live_user'] = w_orm.author
    
    # Prepare author avatar URL (same pattern as image avatars)
    from src.Infrastructure.DjangoFramework.persistence.utils import get_user_avatar
    context['author_name'] = "Alone"
    context['author_avatar_url'] = ""
    if w_orm.author:
        context['author_name'] = w_orm.author.username
        context['author_avatar_url'] = get_user_avatar(w_orm.author, context['jid'])
    
    # CHEQUEO DE PERMISOS
    # NOTA: Los permisos (can_edit, is_admin_role, etc.) ya vienen calculados 
    # robustamente desde GetWorldDetailsUseCase (que usa policies.py).
    # NO debemos sobrescribirlos aquí con lógica simplificada.
    
    # is_admin ya se calcula en el usecase como 'is_admin_role'
    # allow_proposals no se usa mucho, pero si se usara, debería venir del use case intentando unificar.
    # Por seguridad, solo inyectamos lo que NO venga del use case.
    
    if 'can_edit' not in context: # Fallback por si acaso
         context['can_edit'] = is_author_or_team
    # ---------------------------------
    
    # --- OPCIONES DE CREACIÓN PROFUNDA ---
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_available_levels
    context['available_levels'] = get_available_levels(context['jid'])
    # -------------------------------------


    # --- RETOUCH DATA PRE-FILL ---
    if retouch_proposal:
        context['is_retouch_mode'] = True
        context['retouch_proposal'] = retouch_proposal
        
        # Extract properties for metadata manager
        retouch_props = []
        if isinstance(retouch_proposal, TimelinePeriodVersion):
            meta = retouch_proposal.proposed_metadata
            if isinstance(meta, dict):
                retouch_props = [{'key': k, 'value': v} for k, v in meta.items()]
            elif isinstance(meta, list):
                retouch_props = meta
        else:
            # CaosVersionORM
            raw_props = retouch_proposal.cambios.get('metadata', {}).get('properties') or retouch_proposal.cambios.get('properties')
            if raw_props:
                retouch_props = raw_props
        
        if retouch_props:
            context['metadata_obj'] = {'properties': retouch_props}
            # Also update 'props' if it exists in context for visual consistency in viewer
            context['props'] = {p['key']: p['value'] for p in retouch_props}

    return render(request, 'ficha_mundo.html', context)

@login_required
def editar_mundo(request, jid):
    """
    Editor de Entidad: Interfaz para proponer cambios de lore o metadatos técnicos.
    Implementa el flujo de propuestas 'ECLAI' y soporta el modo 'Retoque'
    para corregir versiones rechazadas.
    """
    # Usar helper robusto que intenta Dominio primero, luego PublicID/ID
    w_orm = resolve_jid_orm(jid)
    if not w_orm: return redirect('home')
    
    real_jid = w_orm.id # Ya tenemos el objeto ORM

    # Antigua lógica de retoque eliminada (movida al final para robustez del contexto)
    
    # CHEQUEO DE BLOQUEO
    # El Bypass de Admin solo debe aplicar si tiene acceso de edición legítimo.
    # Como estamos en 'editar_mundo', debemos comprobar si realmente tiene derechos.
    # Nota: 'editar_mundo' aún no llama a check_world_access. Debería.
    
    # CHEQUEO DE BLOQUEO Y PERMISOS DE EDICIÓN
    from src.Infrastructure.DjangoFramework.persistence.policies import can_user_propose_on
    
    can_access, _ = check_world_access(request, w_orm)
    can_propose = can_user_propose_on(request.user, w_orm)
    
    if not can_propose:
         messages.error(request, "⛔ No tienes permisos para editar este mundo.")
         return redirect('ver_mundo', public_id=w_orm.public_id if w_orm.public_id else w_orm.id)

    # is_admin_bypass logic (Superuser/Admin can edit Locked?)
    # Usually only World Owner or Superuser can edit LOCKED.
    # can_user_propose_on grants access to Collaborators too, but locked status overrides that.
    
    can_override_lock = request.user.is_superuser or w_orm.author == request.user
    
    if w_orm.status == 'LOCKED' and not can_override_lock:
        messages.error(request, "⛔ Este mundo está BLOQUEADO por el Autor. No se permiten propuestas.")
        return redirect('ver_mundo', public_id=w_orm.public_id if w_orm.public_id else w_orm.id)

    if request.method == 'POST':
        try:
            w = resolve_jid_orm(jid); real_jid = w.id if w else jid
            desc = request.POST.get('description')
            action_type = request.POST.get('action_type', 'EDIT_WORLD')
            
            metadata_prop = None
            reason = request.POST.get('reason', 'Actualización de Metadatos')
 
            # Manejar Propuesta de Metadatos
            if action_type == 'METADATA_PROPOSAL':
                # NUEVA LÓGICA DINÁMICA (Arrays)
                prop_keys = request.POST.getlist('prop_keys[]')
                prop_values = request.POST.getlist('prop_values[]')
                
                metadata_prop = {'properties': []}
                
                # Unirlos (zip)
                if prop_keys and prop_values:
                    for k, v in zip(prop_keys, prop_values):
                        if k.strip(): # Ignorar claves vacías
                            metadata_prop['properties'].append({'key': k.strip(), 'value': v.strip()})
                
                print(f"📝 [Edición Manual] Enviando Propuesta de Metadatos: {len(metadata_prop['properties'])} elementos.")
                print(f"   Contenido: {metadata_prop}")
                
                # Al editar metadatos, podríamos mantener nombre/desc como están (o usar campos ocultos)
                # Por seguridad, simplemente pasamos None para mantener los valores existentes en el Caso de Uso
                ProposeChangeUseCase().execute(real_jid, None, None, reason, get_current_user(request), metadata_proposal=metadata_prop)
                messages.success(request, f"🔮 Propuesta de METADATOS enviada (v{CaosVersionORM.objects.filter(world_id=real_jid).count() + 1}).")
                log_event(request.user, "PROPOSE_METADATA", real_jid, f"Razón: {reason}")
            else:
                # Edición Regular
                if request.POST.get('use_ai_edit') == 'on':
                    try: desc = Llama3Service().generate_description(f"Nombre: {request.POST.get('name')}. Concepto: {desc}") or desc
                    except: pass
                ProposeChangeUseCase().execute(real_jid, request.POST.get('name'), desc, request.POST.get('reason'), get_current_user(request))
                log_event(request.user, "PROPOSE_CHANGE", real_jid, f"Reason: {request.POST.get('reason')}")
            
            return redirect('ver_mundo', public_id=w.public_id if w.public_id else w.id)
        except Exception as e: 
            print(f"Error de edición: {e}")
            return redirect('home')
 
    # --- GET: RENDERIZAR FORMULARIO DE EDICIÓN ---
    from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
    try:
        # 1. Obtener Contexto Base
        repo = DjangoCaosRepository()
        use_case = GetWorldDetailsUseCase(repo)
        context = use_case.execute(real_jid, request.user)
        
        # 2. Activar Modo Edición
        context['edit_mode'] = True
        
        # 3. Aplicar Sobrescrituras de Retoque (lógica movida aquí por robustez)
        src_version_id = request.GET.get('src_version')
        if src_version_id:
            try:
                v_src = CaosVersionORM.objects.get(id=src_version_id)
                # Verificar propiedad/relación
                can_retouch = (v_src.author == request.user) or is_admin_bypass
                
                if v_src.world.id == real_jid and can_retouch:
                    context['name'] = v_src.proposed_name
                    context['description'] = v_src.proposed_description
                    context['is_retouch_mode'] = True
                    context['can_edit'] = True # Forzar visibilidad del botón Editar
                    messages.info(request, f"✏️ Retomando propuesta rechazada v{v_src.version_number}. Datos cargados.")
            except Exception as e:
                print(f"Error cargando src_version en GET: {e}")
 
        return render(request, 'ficha_mundo.html', context)
    except Exception as e:
        print(f"Error renderizando vista de edición: {e}")
        return redirect('home')



@login_required
def toggle_entity_status(request, jid):
    w = resolve_jid_orm(jid)
    if not w:
        raise Http404("Entidad no encontrada")

    # 1. Verificar Permisos (Superuser o Autor)
    if request.user.is_superuser or w.author == request.user:
        # 2. Cambiar Estado
        if w.status == 'LIVE':
            w.status = 'OFFLINE'
        else:
            w.status = 'LIVE'
        w.save()
        messages.success(request, f"Estado actualizado a: {w.status}")
    else:
        messages.error(request, "Permiso denegado.")

    # 3. REDIRECCIÓN ROBUSTA
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def borrar_mundo(request, jid): 
    try: 
        # Búsqueda Robusta
        # Búsqueda Robusta usando helper estandarizado
        w = resolve_jid_orm(jid)
        if not w:
            messages.error(request, "Entidad no encontrada")
            return redirect('home')
        
        check_ownership(request.user, w) # Chequeo de Seguridad
        
        # Determinar siguiente número de versión
        last_v = w.versiones.order_by('-version_number').first()
        next_v = (last_v.version_number + 1) if last_v else 1
        
        # Crear Propuesta de ELIMINACIÓN
        CaosVersionORM.objects.create(
            world=w,
            proposed_name=w.name,
            proposed_description=w.description,
            version_number=next_v,
            status='PENDING',
            change_log="Solicitud de Eliminación",
            cambios={'action': 'DELETE'},
            author=get_current_user(request)
        )
        
        messages.warning(request, "🗑️ Solicitud de eliminación creada. Ve al Dashboard para confirmar.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error solicitando eliminación: {e}")
        return redirect('home')

@login_required
def toggle_visibilidad(request, jid):
    try: 
        repo = DjangoCaosRepository()
        w_domain = resolve_world_id(repo, jid)
        w = CaosWorldORM.objects.get(id=w_domain.id.value)
        check_ownership(request.user, w) # Chequeo de Seguridad
        
        next_v = CaosVersionORM.objects.filter(world=w).count() + 1
        current_vis = w.visible_publico
        target_vis = not current_vis
        
        CaosVersionORM.objects.create(
            world=w,
            proposed_name=w.name,
            proposed_description=w.description,
            version_number=next_v,
            status='PENDING',
            change_log=f"Solicitud cambio visibilidad: {'PÚBLICO' if target_vis else 'PRIVADO'}",
            cambios={'action': 'TOGGLE_VISIBILITY', 'target_visibility': target_vis},
            author=get_current_user(request)
        )
        
        messages.success(request, "👁️ Solicitud de cambio de visibilidad creada.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error cambiando visibilidad: {e}")
        return redirect('home')

def restaurar_version(request, version_id):
    try:
        v = CaosVersionORM.objects.get(id=version_id)
        RestoreVersionUseCase().execute(version_id, get_current_user(request))
        messages.success(request, "✅ Restaurada.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except: return redirect('home')

def comparar_version(request, version_id):
    try:
        v = CaosVersionORM.objects.get(id=version_id)
        w = v.world
        # Renderizamos la ficha pero con los datos de la versión
        jid = w.id
        safe_pid = w.public_id if w.public_id else jid
        
        imgs = get_world_images(jid)
        
        # Metadata Handling for Preview
        proposed_meta = v.cambios.get('metadata', {}) if v.cambios else {}
        live_meta = w.metadata if w.metadata else {}
        
        # Calculate Metadata Version
        # Count all previous versions of this world that had metadata changes
        meta_count = CaosVersionORM.objects.filter(
            world=w, 
            version_number__lte=v.version_number
        ).filter(
            Q(cambios__has_key='metadata') | Q(cambios__action='METADATA_UPDATE')
        ).count()
        
        # Special case: if this version doesn't have metadata changes but we are previewing it,
        # we still show the metadata at that point in time (V count).
        
        # Prepare Decorated Metadata List for Template
        # v.cambios might have 'metadata' key (which is a dict with 'properties')
        proposed_meta = v.cambios.get('metadata', {}) if v.cambios else {}
        live_meta = w.metadata if w.metadata else {}
        
        from .view_utils import get_metadata_properties_dict
        proposed_props = get_metadata_properties_dict(proposed_meta)
        live_props = get_metadata_properties_dict(live_meta)
        
        diff_results = get_metadata_diff(live_meta, proposed_meta) if proposed_meta else []
        diff_map = {d['key']: d for d in diff_results}
        
        metadata_list = []
        # If we have a proposal, show it with decorations 
        # (Fall back to live properties for those not changed if it was an update? 
        # Actually usually it's a full replacement in this system).
        
        # We decide what to show based on all available keys
        all_keys = sorted(set(proposed_props.keys()) | set(live_props.keys()))
        
        for key in all_keys:
            action = diff_map.get(key, {}).get('action', 'NORMAL')
            val = proposed_props.get(key, live_props.get(key))
            
            # If it was deleted, show old value
            if action == 'DELETE':
                val = live_props.get(key)
                
            metadata_list.append({
                'key': key,
                'value': val,
                'action': action
            })
            
        # Prepare Context with Permissions
        is_admin, is_team_member = get_admin_status(request.user)
        
        context = {
            'name': v.proposed_name,
            'description': v.proposed_description,
            'jid': jid, 'public_id': safe_pid,
            'status': f"PREVIEW v{v.version_number} ({v.status})",
            'version_live': w.current_version_number,
            'author_live': v.author.username if v.author else "Desconocido",
            'created_at': v.created_at, 'updated_at': v.created_at,
            'visible': False, 
            'nid_lore': w.id_lore,
            'metadata_obj': {'properties': metadata_list},
            'metadata_version': f"V{meta_count}" if meta_count > 0 else "V0",
            'is_preview': True, 
            'preview_version_id': v.id,
            'breadcrumbs': generate_breadcrumbs(jid),
            'imagenes': imgs, 'hijos': [],
            
            # Permisos y Estados para UI
            'status_str': 'PREVIEW',
            'author_live_user': v.author,
            'is_author': is_author_or_team,
            'is_admin_role': is_admin,
            'can_edit': False, # No editar durante previsualización
            'allow_proposals': False, # No proponer sobre una previsualización
            'user_role': request.user.profile.rank_value if hasattr(request.user, 'profile') else 0
        }
        
        # --- INYECCIÓN DE ETIQUETA DE JERARQUÍA ---
        context['hierarchy_label'] = get_readable_hierarchy(jid)
        # ------------------------------------------
        
        messages.info(request, f"👀 Viendo PREVISUALIZACIÓN de versión {v.version_number}")
        return render(request, 'ficha_mundo.html', context)
    except Exception as e: 
        print(e)
        return redirect('home')

@login_required
def init_hemisferios(request, jid):
    try: 
        w=resolve_jid_orm(jid)
        w_orm = CaosWorldORM.objects.get(id=w.id)
        check_ownership(request.user, w_orm)
        InitializeHemispheresUseCase(DjangoCaosRepository()).execute(w.id); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')

def escanear_planeta(request, jid): return redirect('ver_mundo', public_id=jid)

def mapa_arbol(request, public_id):
    try:
        repo = DjangoCaosRepository()
        # Chequeo de Seguridad
        w_orm = resolve_jid_orm(public_id)
        if not w_orm: return redirect('home')
        
        can_access, _ = check_world_access(request, w_orm)
        if not can_access: 
             return render(request, 'private_access.html', status=403)

        result = GetWorldTreeUseCase(repo).execute(public_id)
        if not result: return redirect('home')
        return render(request, 'mapa_arbol.html', result)
    except Http404: raise
    except: return redirect('ver_mundo', public_id=public_id)

@login_required
def toggle_lock(request, jid):
    
    w_orm = resolve_jid_orm(jid)
    if not w_orm:
        raise Http404("Entidad no encontrada")

    # CHEQUEO DE PERMISOS: Solo el Autor o Superusuario
    # (Admins no pueden bloquear mundos ajenos, solo Superusuarios)
    can_lock = request.user.is_superuser or (w_orm.author == request.user)
        
    if not can_lock:
        messages.error(request, "⛔ Solo el Autor o Superadmin pueden bloquear.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    # Lógica de Bloqueo
    if w_orm.status == 'LOCKED':
        w_orm.status = 'OFFLINE' # Desbloquear a estado seguro
        messages.success(request, "🔓 Mundo desbloqueado (OFFLINE).")
    else:
        w_orm.status = 'LOCKED'
        messages.warning(request, "🔒 Mundo BLOQUEADO.")
    
    w_orm.save()
    
    # CRÍTICO: Redirigir a la página desde donde se hizo clic
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# @login_required (Eliminado para acceso público LIVE)
def ver_metadatos(request, public_id):
    w = resolve_jid_orm(public_id)
    if not w: return redirect('home')

    # Chequeo de Seguridad
    can_access, _ = check_world_access(request, w)
    if not can_access: 
        return render(request, 'private_access.html', status=403)
    
    context = {
        'name': w.name,
        'public_id': w.public_id,
        'jid': w.id,
        'metadata_template': None
    }
    
    # --- INYECCIÓN DE ETIQUETA DE JERARQUÍA ---
    context['hierarchy_label'] = get_readable_hierarchy(w.id)
    # ------------------------------------------
    
    # Cargar Metadatos (Reutilizar lógica)
    if w.id == "01" or "Caos" in w.name:
         tpl = MetadataTemplate.objects.filter(entity_type='CHAOS').first()
         if tpl:
             context['metadata_template'] = {
                'entity_type': tpl.entity_type,
                'schema': tpl.schema_definition,
                # En la aplicación real, recuperar los valores de metadatos almacenados de w.metadata
             }
             context['metadata_obj'] = {} 
    
    return render(request, 'ver_metadatos.html', context)

