"""
API Endpoints para el sistema de propuestas Timeline.

Este módulo proporciona endpoints REST para:
- Crear propuestas de snapshots temporales
- Listar propuestas de Timeline
- Aprobar/Rechazar propuestas de Timeline
- Obtener detalles de propuestas
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from src.Shared.Services.ProposalService import TimelineProposalService, ProposalService
from src.Shared.Services.MetadataValidator import validate_timeline_snapshot
import json
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CREAR PROPUESTA DE TIMELINE
# ============================================================================

@require_http_methods(["POST"])
@login_required
@csrf_exempt
def create_timeline_proposal(request, world_id):
    """
    Crea una nueva propuesta de snapshot temporal.
    
    POST /api/world/{world_id}/timeline/propose
    
    Body:
    {
        "year": 1500,
        "description": "En el año 1500...",
        "metadata": {
            "datos_nucleo": {
                "poblacion": "10000",
                "gobierno": "Monarquía"
            }
        },
        "images": ["image1.webp", "image2.png"],
        "cover_image": "image1.webp",
        "change_log": "Añadir período histórico"
    }
    
    Response:
    {
        "success": true,
        "proposal_id": 123,
        "message": "Propuesta de snapshot creada exitosamente"
    }
    """
    try:
        # Parsear body
        data = json.loads(request.body)
        
        # Validar campos requeridos
        required_fields = ['year', 'description', 'metadata']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return JsonResponse({
                'success': False,
                'error': f'Faltan campos requeridos: {", ".join(missing_fields)}'
            }, status=400)
        
        # Obtener entidad
        try:
            world = CaosWorldORM.objects.get(public_id=world_id, is_active=True)
        except CaosWorldORM.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Entidad no encontrada'
            }, status=404)
        
        # Verificar permisos (el usuario debe poder proponer cambios)
        if not world.allow_proposals and world.author != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Esta entidad no permite propuestas de terceros'
            }, status=403)
        
        # Construir snapshot
        snapshot = {
            'description': data['description'],
            'metadata': data['metadata'],
            'images': data.get('images', []),
            'cover_image': data.get('cover_image')
        }
        
        # Validar snapshot
        is_valid, error = validate_timeline_snapshot(snapshot)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': f'Snapshot inválido: {error}'
            }, status=400)
        
        # Crear propuesta
        try:
            proposal = TimelineProposalService.create_proposal(
                world=world,
                year=int(data['year']),
                snapshot=snapshot,
                author=request.user,
                change_log=data.get('change_log', '')
            )
            
            logger.info(f"✅ Propuesta Timeline creada: {proposal.id} por {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'proposal_id': proposal.id,
                'year': proposal.timeline_year,
                'status': proposal.status,
                'message': 'Propuesta de snapshot creada exitosamente'
            }, status=201)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"❌ Error creando propuesta Timeline: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


# ============================================================================
# LISTAR PROPUESTAS DE TIMELINE
# ============================================================================

@require_http_methods(["GET"])
@login_required
def list_timeline_proposals(request):
    """
    Lista propuestas de Timeline con filtros opcionales.
    
    GET /api/timeline/proposals?status=PENDING&world_id=abc123
    
    Query params:
    - status: PENDING, APPROVED, REJECTED, PUBLISHED
    - world_id: Filtrar por entidad específica
    - author: Filtrar por autor
    
    Response:
    {
        "success": true,
        "count": 10,
        "proposals": [
            {
                "id": 123,
                "world_id": "abc123",
                "world_name": "Jade",
                "year": 1500,
                "status": "PENDING",
                "author": "usuario123",
                "created_at": "2025-12-29T10:00:00Z",
                "change_log": "Añadir período histórico"
            }
        ]
    }
    """
    try:
        # Obtener parámetros de filtro
        status = request.GET.get('status')
        world_id = request.GET.get('world_id')
        author_username = request.GET.get('author')
        
        # Query base
        queryset = CaosVersionORM.objects.filter(
            change_type='TIMELINE'
        ).select_related('world', 'author').order_by('-created_at')
        
        # Aplicar filtros
        if status:
            queryset = queryset.filter(status=status)
        
        if world_id:
            queryset = queryset.filter(world__public_id=world_id)
        
        if author_username:
            queryset = queryset.filter(author__username=author_username)
        
        # Filtrar por permisos (usuarios normales solo ven sus propias propuestas)
        if not request.user.is_staff:
            queryset = queryset.filter(author=request.user)
        
        # Serializar
        proposals = []
        for p in queryset:
            proposals.append({
                'id': p.id,
                'world_id': p.world.public_id,
                'world_name': p.world.name,
                'year': p.timeline_year,
                'status': p.status,
                'author': p.author.username if p.author else 'Sistema',
                'created_at': p.created_at.isoformat(),
                'change_log': p.change_log,
                'snapshot_preview': {
                    'description': p.proposed_snapshot.get('description', '')[:100] + '...' if p.proposed_snapshot else '',
                    'has_images': len(p.proposed_snapshot.get('images', [])) > 0 if p.proposed_snapshot else False
                }
            })
        
        return JsonResponse({
            'success': True,
            'count': len(proposals),
            'proposals': proposals
        })
        
    except Exception as e:
        logger.error(f"❌ Error listando propuestas Timeline: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


# ============================================================================
# OBTENER DETALLE DE PROPUESTA
# ============================================================================

@require_http_methods(["GET"])
@login_required
def get_timeline_proposal_detail(request, proposal_id):
    """
    Obtiene detalles completos de una propuesta de Timeline.
    
    GET /api/timeline/proposal/{proposal_id}
    
    Response:
    {
        "success": true,
        "proposal": {
            "id": 123,
            "world": {...},
            "year": 1500,
            "status": "PENDING",
            "snapshot": {...},
            "author": "usuario123",
            "created_at": "...",
            "reviewer": null,
            "admin_feedback": ""
        }
    }
    """
    try:
        # Obtener propuesta
        try:
            proposal = CaosVersionORM.objects.select_related(
                'world', 'author', 'reviewer'
            ).get(id=proposal_id, change_type='TIMELINE')
        except CaosVersionORM.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Propuesta no encontrada'
            }, status=404)
        
        # Verificar permisos
        if not request.user.is_staff and proposal.author != request.user:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permiso para ver esta propuesta'
            }, status=403)
        
        # Serializar
        data = {
            'id': proposal.id,
            'world': {
                'id': proposal.world.public_id,
                'name': proposal.world.name,
                'current_description': proposal.world.description
            },
            'year': proposal.timeline_year,
            'status': proposal.status,
            'snapshot': proposal.proposed_snapshot,
            'author': proposal.author.username if proposal.author else 'Sistema',
            'created_at': proposal.created_at.isoformat(),
            'change_log': proposal.change_log,
            'reviewer': proposal.reviewer.username if proposal.reviewer else None,
            'admin_feedback': proposal.admin_feedback,
            'version_number': proposal.version_number
        }
        
        return JsonResponse({
            'success': True,
            'proposal': data
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalle de propuesta: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


# ============================================================================
# APROBAR PROPUESTA DE TIMELINE
# ============================================================================

@require_http_methods(["POST"])
@login_required
@csrf_exempt
def approve_timeline_proposal(request, proposal_id):
    """
    Aprueba y publica una propuesta de Timeline.
    
    POST /api/timeline/proposal/{proposal_id}/approve
    
    Response:
    {
        "success": true,
        "message": "Snapshot del año 1500 publicado exitosamente"
    }
    """
    try:
        # Verificar permisos (solo staff puede aprobar)
        if not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para aprobar propuestas'
            }, status=403)
        
        # Obtener propuesta
        try:
            proposal = CaosVersionORM.objects.get(
                id=proposal_id,
                change_type='TIMELINE'
            )
        except CaosVersionORM.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Propuesta no encontrada'
            }, status=404)
        
        # Aprobar y publicar
        try:
            TimelineProposalService.approve_and_publish(proposal, reviewer=request.user)
            
            logger.info(f"✅ Propuesta Timeline {proposal_id} aprobada por {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'message': f'Snapshot del año {proposal.timeline_year} publicado exitosamente',
                'year': proposal.timeline_year,
                'world_id': proposal.world.public_id
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
    except Exception as e:
        logger.error(f"❌ Error aprobando propuesta Timeline: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


# ============================================================================
# RECHAZAR PROPUESTA DE TIMELINE
# ============================================================================

@require_http_methods(["POST"])
@login_required
@csrf_exempt
def reject_timeline_proposal(request, proposal_id):
    """
    Rechaza una propuesta de Timeline.
    
    POST /api/timeline/proposal/{proposal_id}/reject
    
    Body:
    {
        "feedback": "Razón del rechazo"
    }
    
    Response:
    {
        "success": true,
        "message": "Propuesta rechazada"
    }
    """
    try:
        # Verificar permisos
        if not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para rechazar propuestas'
            }, status=403)
        
        # Parsear body
        data = json.loads(request.body)
        feedback = data.get('feedback', '')
        
        # Obtener propuesta
        try:
            proposal = CaosVersionORM.objects.get(
                id=proposal_id,
                change_type='TIMELINE'
            )
        except CaosVersionORM.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Propuesta no encontrada'
            }, status=404)
        
        # Rechazar
        try:
            TimelineProposalService.reject(proposal, reviewer=request.user, feedback=feedback)
            
            logger.info(f"❌ Propuesta Timeline {proposal_id} rechazada por {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'message': 'Propuesta rechazada',
                'feedback': feedback
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"❌ Error rechazando propuesta Timeline: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)
