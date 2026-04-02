"""
Vistas de listado e índices de mundos.
"""
import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.utils.timezone import localtime
from django.db.models import Q, Case, When, Value, IntegerField, Count
from django.db.models.functions import Length

from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, CaosVersionORM, CaosNarrativeORM, CaosEventLog, 
    MetadataTemplate, TimelinePeriodVersion, CaosLike, UserProfile, CaosComment, Message
)
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.Shared.Services.SocialService import SocialService
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.generate_creature_usecase import GenerateCreatureUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
from src.WorldManagement.Caos.Application.toggle_visibility import ToggleWorldVisibilityUseCase
from src.WorldManagement.Caos.Application.toggle_lock import ToggleWorldLockUseCase
from src.WorldManagement.Caos.Application.get_world_tree import GetWorldTreeUseCase
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs, get_world_images
from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
from src.FantasyWorld.Domain.Services.EntityService import EntityService
from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy
from ..view_utils import resolve_jid_orm, check_world_access, get_admin_status, get_metadata_diff
from .utils import log_event, get_current_user


def landing(request):
    """
    Portal de Entrada: Vista de Bienvenida con Selección de Destino.
    Recupera un pool de imágenes de mundos para usarlas como fondos dinámicos.
    """
    mundos = CaosWorldORM.objects.filter(is_active=True).exclude(status='DELETED')
    
    background_pool = []
    for m in mundos:
        imgs = get_world_images(m.id, world_instance=m)
        cover = None
        if m.metadata and 'cover_image' in m.metadata:
            target = m.metadata['cover_image']
            found = next((i for i in imgs if i['filename'] == target), None)
            if found: cover = found['url']
        
        if not cover and imgs:
            imgs.sort(key=lambda x: x.get('is_cover', False), reverse=True)
            cover = imgs[0]['url']
            
        if cover:
            background_pool.append(cover)

    import random
    random.shuffle(background_pool)
    
    # Seleccionar 2 imágenes aleatorias para las puertas
    img_nexo = background_pool[0] if len(background_pool) > 0 else None
    img_codice = background_pool[1] if len(background_pool) > 1 else (img_nexo or None)
    
    context = {
        'img_nexo': img_nexo,
        'img_codice': img_codice,
        'background_images': background_pool[:10] 
    }
    
    return render(request, 'index.html', context)


def home(request):
    """
    Vista de Inicio: El Portal Central del Universo.
    Muestra el índice de mundos habitables y gestiona la creación del Planet Wizard.
    """
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        repo = DjangoCaosRepository()
        
        # Recolectar metadatos geofísicos del Paso 2 del Wizard
        planet_metadata = {
            'planet_laws': {
                'global_temp': request.POST.get('world_temp', 'Templado'),
                'sun_type': request.POST.get('world_sun', 'Gigante Amarilla'),
                'base_element': request.POST.get('world_element', 'Agua'),
                'moons': [m.strip() for m in request.POST.get('world_moons', '').split(',') if m.strip()],
                'axial_tilt': request.POST.get('world_tilt', 'Moderada'),
            }
        }

        try:
            jid = CreateWorldUseCase(repo).execute(
                name=request.POST.get('world_name'), 
                description=request.POST.get('world_desc'),
                author=request.user,
                metadata=planet_metadata
            )
            w = CaosWorldORM.objects.get(id=jid)
            w.author = request.user
            w.save()
            messages.success(request, f"✨ Planeta '{w.name}' creado e inicializado en la Era 0.")
        except Exception as e:
            messages.error(request, f"Error al proponer mundo: {str(e)}")
            
        return redirect('dashboard')
    
    # Mostrar mundos 'LIVE'
    ms = CaosWorldORM.objects.filter(is_active=True).exclude(status='DELETED')
    
    # Exclusión de descripciones vacías, EXCEPTO para Caos Prime
    ms = ms.exclude(
        Q(description__isnull=True) | Q(description__exact='') | Q(description__iexact='None'),
        ~Q(public_id='JhZCO1vxI7')
    )
    
    ms = ms.exclude(id__endswith='00', name__startswith='Nexo Fantasma') \
        .exclude(id__endswith='00', name__startswith='Ghost')
    
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
            'name'
        )

    from src.Infrastructure.DjangoFramework.persistence.policies import get_visibility_q_filter
    q_filter = get_visibility_q_filter(request.user)
    ms = ms.filter(q_filter)

    from src.WorldManagement.Caos.Application.get_home_index import GetHomeIndexUseCase
    use_case = GetHomeIndexUseCase()
    final_list = use_case.execute(ms)

    l = []
    background_images = []
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_plural_label

    for m in final_list:
        imgs = get_world_images(m.id, world_instance=m)
        cover = imgs[0]['url'] if imgs else None
        if m.metadata and 'cover_image' in m.metadata:
            target = m.metadata['cover_image']
            found = next((i for i in imgs if i['filename'] == target), None)
            if found: cover = found['url']
        
        if cover: background_images.append(cover)
  
        entity_images = [i['url'] for i in imgs] if imgs else []
        if cover and cover in entity_images:
            entity_images.remove(cover)
            entity_images.insert(0, cover)
        
        visual_name = get_plural_label(len(m.id)//2, m.id)
        if len(m.id)//2 == 1: visual_name = "CAOS"

        pid = m.public_id if m.public_id else m.id
        l.append({
            'id': m.id, 
            'public_id': pid, 
            'name': visual_name, 
            'real_name': m.name,
            'status': m.status, 
            'img': cover,
            'images': entity_images[:5], 
            'has_img': bool(cover), 
            'visible': m.visible_publico,
            'is_locked': m.status == 'LOCKED',
            'author': m.author,
            'level': len(m.id)//2,
        })
    
    import random
    random.shuffle(background_images)
    
    return render(request, 'nexo_list.html', {'mundos': l, 'background_images': background_images[:10]})
