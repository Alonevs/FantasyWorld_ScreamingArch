from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id

def resolve_jid_orm(identifier) -> CaosWorldORM:
    """
    Resuelve un J-ID o PublicID (NanoID) a una instancia de CaosWorldORM.
    Devuelve None si no se encuentra.
    """
    repo = DjangoCaosRepository()
    w_domain = resolve_world_id(repo, identifier)
    if w_domain:
        try:
            return CaosWorldORM.objects.get(id=w_domain.id.value)
        except CaosWorldORM.DoesNotExist:
            return None
            
    # Fallback: Intentar identificar como NanoID o ID directo
    try:
        # Intentar por public_id (NanoID)
        return CaosWorldORM.objects.get(public_id=identifier)
    except CaosWorldORM.DoesNotExist:
        try:
            # Intentar ID plano (Entero/Legacy)
            return CaosWorldORM.objects.get(id=identifier)
        except (CaosWorldORM.DoesNotExist, ValueError):
            return None
    return None

def check_world_access(request, world_orm: CaosWorldORM):
    """
    Verifica si el usuario actual tiene acceso para ver un mundo.
    Reglas: 
    1. El estado 'LIVE' es público.
    2. Otros estados requieren:
       - Ser el autor
       - Ser colaborador del autor
       - Ser superusuario
    Devuelve (can_access: bool, is_author_or_team: bool)
    """
    if not world_orm:
        return False, False

    is_live = (world_orm.status == 'LIVE')
    is_superuser = request.user.is_superuser
    is_authenticated = request.user.is_authenticated
    
    is_strict_author = (is_authenticated and world_orm.author == request.user)
    
    # Acceso Delegado (Sub-Admin / Colaborador)
    # Si soy colaborador del Autor, tengo acceso total (Ver/Editar)
    is_collaborator = False
    if is_authenticated and not is_strict_author and world_orm.author:
        # Comprobar colaboración explícita vía Perfil
        # Relación Correcta: El Author.profile.collaborators me contiene (Me.profile)
        try:
            if hasattr(world_orm.author, 'profile') and hasattr(request.user, 'profile'):
                if request.user.profile in world_orm.author.profile.collaborators.all():
                    is_collaborator = True
        except: pass

    
    # Acceso de Admin GLOBAL (Solo Superusuario)
    # El rango 'ADMIN' ahora está en Silo (como un Usuario con funciones extra de dashboard), 
    # por lo que no pueden editar/ver el contenido privado de otros Admins.
    is_global_admin = False
    if is_authenticated and request.user.is_superuser:
        is_global_admin = True

    is_author_or_team = is_strict_author or is_collaborator or is_global_admin
    
    # Acceso Público Estricto: Debe ser LIVE Y marcado explícitamente como visible_publico
    is_publicly_visible = (is_live and world_orm.visible_publico)
    
    can_access = is_publicly_visible or is_author_or_team
    
    return can_access, is_author_or_team

def get_admin_status(user):
    """Verifica si el usuario tiene rango ADMIN o SUBADMIN."""
    if not user.is_authenticated:
        return False, False
    
    try:
        rank = user.profile.rank
        return rank == 'ADMIN', rank in ['ADMIN', 'SUBADMIN']
    except:
        return False, False
