from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosEventLog
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id

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

    # LÓGICA CENTRALIZADA (policies.py)
    from src.Infrastructure.DjangoFramework.persistence.policies import can_user_view_world, get_user_access_level
    
    can_access = can_user_view_world(request.user, world_orm)
    
    # Flags auxiliares para UI (Is Author/Team) -> Usados para ocultar/mostrar ciertos controles menores
    access_level = get_user_access_level(request.user, world_orm)
    is_author_or_team = (access_level in ['OWNER', 'COLLABORATOR', 'SUPERUSER'])
    
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

def get_metadata_diff(old_meta, new_meta):
    """
    Compara dos diccionarios de metadatos y devuelve una lista de cambios.
    old_meta/new_meta: {'properties': [{'key': '...', 'value': '...'}, ...]}
    """
    old_props = get_metadata_properties_dict(old_meta)
    new_props = get_metadata_properties_dict(new_meta)
    
    diff = []
    all_keys = sorted(set(old_props.keys()) | set(new_props.keys()))
    
    for key in all_keys:
        old_val = old_props.get(key)
        new_val = new_props.get(key)
        
        if old_val is None:
            diff.append({'key': key, 'action': 'ADD', 'new': new_val})
        elif new_val is None:
            diff.append({'key': key, 'action': 'DELETE', 'old': old_val})
        elif old_val != new_val:
            diff.append({'key': key, 'action': 'CHANGE', 'old': old_val, 'new': new_val})
            
    return diff

def get_metadata_properties_dict(raw_meta):
    """
    Adapta cualquier formato de metadatos (V1, V2.0, V2.1) a un diccionario plano {key: value}.
    """
    if not isinstance(raw_meta, dict): return {}
    
    props = {}
    # CASO V2.1: {'properties': [...]}
    if 'properties' in raw_meta and isinstance(raw_meta['properties'], list):
        for p in raw_meta['properties']:
            if isinstance(p, dict) and 'key' in p:
                props[p['key']] = p.get('value', '')
    
    # CASO V2.0: {'datos_nucleo': {...}, 'datos_extendidos': {...}}
    elif 'datos_nucleo' in raw_meta:
        nucleo = raw_meta.get('datos_nucleo', {})
        if isinstance(nucleo, dict): props.update(nucleo)
        extendidos = raw_meta.get('datos_extendidos', {})
        if isinstance(extendidos, dict): props.update(extendidos)
        if 'tipo_entidad' in raw_meta: props['TIPO_ENTIDAD'] = raw_meta['tipo_entidad']
        
    # CASO V1.0: Plano
    else:
        for k, v in raw_meta.items():
            if k not in ['cover_image', 'images', 'properties']:
                props[k] = v
                
    return props
