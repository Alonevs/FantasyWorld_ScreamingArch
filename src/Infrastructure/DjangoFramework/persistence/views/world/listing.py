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
