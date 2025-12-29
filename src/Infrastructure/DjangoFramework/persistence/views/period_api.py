"""
API endpoints para gestionar períodos temporales (Timeline Periods).
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import json

from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM,
    TimelinePeriod,
    TimelinePeriodVersion
)
from src.Shared.Services.TimelinePeriodService import TimelinePeriodService


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_period(request, world_id):
    """
    Crea un nuevo período temporal para una entidad.
    
    POST /api/world/{world_id}/period/create
    Body: {
        "title": "Inicios",
        "description": "En los inicios...",
        "order": 1  // opcional
    }
    """
    try:
        world = get_object_or_404(CaosWorldORM, public_id=world_id)
        data = json.loads(request.body)
        
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        order = data.get('order')
        
        # Validaciones
        if not title:
            return JsonResponse({'error': 'El título es obligatorio'}, status=400)
        
        if len(title) > 100:
            return JsonResponse({'error': 'El título no puede exceder 100 caracteres'}, status=400)
        
        # Crear período
        period = TimelinePeriodService.create_period(
            world=world,
            title=title,
            description=description,
            author=request.user,
            order=order
        )
        
        return JsonResponse({
            'success': True,
            'period': {
                'id': period.id,
                'title': period.title,
                'slug': period.slug,
                'description': period.description,
                'order': period.order,
                'is_current': period.is_current,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def propose_period_edit(request, period_id):
    """
    Propone cambios a un período existente.
    
    POST /api/period/{period_id}/propose
    Body: {
        "title": "Nuevo título",  // opcional
        "description": "Nueva descripción",  // opcional
        "change_log": "Razón del cambio"
    }
    """
    try:
        period = get_object_or_404(TimelinePeriod, id=period_id)
        data = json.loads(request.body)
        
        title = data.get('title', '').strip() or None
        description = data.get('description', '').strip() or None
        change_log = data.get('change_log', '').strip()
        metadata = data.get('metadata')
        
        # Validar que al menos uno de los campos cambie
        if not title and not description and metadata is None:
            return JsonResponse({
                'error': 'Debes proponer al menos un cambio (título, descripción o metadatos)'
            }, status=400)
        
        # Crear propuesta
        version = TimelinePeriodService.propose_edit(
            period=period,
            title=title,
            description=description,
            metadata=metadata,
            author=request.user,
            change_log=change_log
        )
        
        return JsonResponse({
            'success': True,
            'version': {
                'id': version.id,
                'version_number': version.version_number,
                'status': version.status,
                'proposed_title': version.proposed_title,
                'proposed_description': version.proposed_description,
                'change_log': version.change_log,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_period_detail(request, period_id):
    """
    Obtiene detalles de un período específico.
    
    GET /api/period/{period_id}/
    """
    try:
        period = get_object_or_404(TimelinePeriod, id=period_id)
        
        # Obtener versiones
        versions = period.versions.all().order_by('-version_number')[:10]
        
        return JsonResponse({
            'period': {
                'id': period.id,
                'title': period.title,
                'slug': period.slug,
                'description': period.description,
                'order': period.order,
                'is_current': period.is_current,
                'cover_image': period.cover_image,
                'created_at': period.created_at.isoformat(),
                'updated_at': period.updated_at.isoformat(),
                'current_version': period.current_version_number,
                'world': {
                    'id': period.world.id,
                    'name': period.world.name,
                    'public_id': period.world.public_id,
                }
            },
            'versions': [
                {
                    'id': v.id,
                    'version_number': v.version_number,
                    'status': v.status,
                    'proposed_title': v.proposed_title,
                    'proposed_description': v.proposed_description[:200] + '...' if len(v.proposed_description) > 200 else v.proposed_description,
                    'author': v.author.username if v.author else 'Desconocido',
                    'created_at': v.created_at.isoformat(),
                }
                for v in versions
            ]
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def approve_period_version(request, version_id):
    """
    Aprueba una versión propuesta de un período.
    Solo admins pueden aprobar.
    
    POST /api/period/version/{version_id}/approve
    """
    try:
        # Verificar permisos de admin
        if not (request.user.is_superuser or 
                (hasattr(request.user, 'profile') and request.user.profile.rank in ['ADMIN', 'SUPERADMIN'])):
            return JsonResponse({'error': 'No tienes permisos para aprobar'}, status=403)
        
        version = get_object_or_404(TimelinePeriodVersion, id=version_id)
        
        # Aprobar
        period = TimelinePeriodService.approve_version(version, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Versión aprobada y período actualizado',
            'period': {
                'id': period.id,
                'title': period.title,
                'description': period.description,
                'current_version': period.current_version_number,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def reject_period_version(request, version_id):
    """
    Rechaza una versión propuesta de un período.
    Solo admins pueden rechazar.
    
    POST /api/period/version/{version_id}/reject
    Body: {
        "feedback": "Razón del rechazo"
    }
    """
    try:
        # Verificar permisos de admin
        if not (request.user.is_superuser or 
                (hasattr(request.user, 'profile') and request.user.profile.rank in ['ADMIN', 'SUPERADMIN'])):
            return JsonResponse({'error': 'No tienes permisos para rechazar'}, status=403)
        
        version = get_object_or_404(TimelinePeriodVersion, id=version_id)
        data = json.loads(request.body)
        feedback = data.get('feedback', '').strip()
        
        # Rechazar
        version = TimelinePeriodService.reject_version(version, request.user, feedback)
        
        return JsonResponse({
            'success': True,
            'message': 'Versión rechazada',
            'version': {
                'id': version.id,
                'status': version.status,
                'admin_feedback': version.admin_feedback,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["DELETE", "POST"])
def delete_period(request, period_id):
    """
    Elimina un período temporal (Directo si es Admin via DELETE, o Propuesta via POST).
    """
    period = get_object_or_404(TimelinePeriod, id=period_id)
    
    if request.method == 'DELETE':
        try:
            # Verificar permisos para borrado directo
            if not (request.user.is_superuser or 
                    (hasattr(request.user, 'profile') and request.user.profile.rank in ['ADMIN', 'SUPERADMIN'])):
                return JsonResponse({'error': 'No tienes permisos para eliminar directamente'}, status=403)
            
            TimelinePeriodService.delete_period(period)
            return JsonResponse({'success': True, 'message': 'Período eliminado correctamente'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    elif request.method == 'POST':
        # Propuesta de Borrado
        try:
            reason = request.POST.get('reason') or request.GET.get('reason') or "Eliminación solicitada desde la interfaz."
            version = TimelinePeriodService.propose_delete(period, request.user, reason)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': True, 'message': 'Propuesta de borrado enviada', 'id': version.id})
                
            messages.success(request, f"🗑️ Propuesta de borrado para '{period.title}' enviada.")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('dashboard')


@require_http_methods(["GET"])
def list_world_periods(request, world_id):
    """
    Lista todos los períodos de una entidad.
    
    GET /api/world/{world_id}/periods
    """
    try:
        world = get_object_or_404(CaosWorldORM, id=world_id)
        periods = TimelinePeriodService.get_periods_for_world(world)
        
        return JsonResponse({
            'periods': [
                {
                    'id': p.id,
                    'title': p.title,
                    'slug': p.slug,
                    'description': p.description[:200] + '...' if len(p.description) > 200 else p.description,
                    'order': p.order,
                    'is_current': p.is_current,
                    'current_version': p.current_version_number,
                }
                for p in periods
            ]
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
