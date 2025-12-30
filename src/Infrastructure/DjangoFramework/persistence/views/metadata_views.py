from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import models
import json

from ..models import CaosWorldORM, TimelinePeriod, CaosVersionORM, TimelinePeriodVersion
from .view_utils import resolve_jid_orm
from src.Shared.Services.TimelinePeriodService import TimelinePeriodService

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def propose_metadata_update(request, target_type, target_id):
    """
    Propone un cambio de metadata para un Mundo (Actual) o un Periodo.
    target_type: 'WORLD' o 'PERIOD'
    target_id: public_id del mundo o id del periodo
    """
    try:
        data = json.loads(request.body)
        proposed_metadata = data.get('metadata', {})
        change_log = data.get('change_log', 'Cambio de metadata independiente')
        
        if not proposed_metadata:
            return JsonResponse({'error': 'No se enviaron metadatos para proponer'}, status=400)

        if target_type == 'WORLD':
            world = resolve_jid_orm(target_id)
            if not world:
                return JsonResponse({'error': 'Mundo no encontrado'}, status=404)
            
            # Encontrar el número de versión siguiente
            last_v = CaosVersionORM.objects.filter(world=world).aggregate(models.Max('version_number'))['version_number__max'] or 0
            
            proposal = CaosVersionORM.objects.create(
                world=world,
                proposed_name=world.name,
                proposed_description=world.description,
                version_number=last_v + 1,
                status='PENDING',
                change_log=change_log,
                change_type='METADATA',
                cambios={'metadata': proposed_metadata},
                author=request.user
            )
            return JsonResponse({
                'success': True, 
                'version_id': proposal.id, 
                'version_number': proposal.version_number
            })

        elif target_type == 'PERIOD':
            period = get_object_or_404(TimelinePeriod, id=target_id)
            
            # Usamos el servicio de periodos para crear la propuesta
            version = TimelinePeriodService.propose_edit(
                period=period,
                title=None, # No cambia el título
                description=None, # No cambia la descripción
                metadata=proposed_metadata,
                author=request.user,
                change_log=change_log
            )
            
            return JsonResponse({
                'success': True, 
                'version_id': version.id, 
                'version_number': version.version_number
            })

        return JsonResponse({'error': 'Tipo de objetivo no válido'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
