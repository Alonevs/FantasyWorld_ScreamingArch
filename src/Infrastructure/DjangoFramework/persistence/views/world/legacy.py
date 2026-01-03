"""
Funciones legacy (deprecadas, mantener por compatibilidad).
TODO: Migrar o eliminar en futuras versiones.
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


@login_required
def init_hemisferios(request, jid):
    try: 
        w=resolve_jid_orm(jid)
        w_orm = CaosWorldORM.objects.get(id=w.id)
        check_ownership(request.user, w_orm)
        InitializeHemispheresUseCase(DjangoCaosRepository()).execute(w.id); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')

def escanear_planeta(request, jid): return redirect('ver_mundo', public_id=jid)
