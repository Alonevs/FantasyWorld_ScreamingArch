import os
import json
import base64
import io
import logging
from PIL import Image
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosEventLog, CaosImageProposalORM, CaosVersionORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from .view_utils import resolve_jid_orm

# Removed local resolve_jid, using resolve_jid_orm instead

def log_event(user, action, target_id, details=""):
    try:
        u = user if user.is_authenticated else None
        CaosEventLog.objects.create(user=u, action=action, target_id=target_id, details=details)
    except Exception as e: logger.error(f"Log Error: {e}", exc_info=True)

@csrf_exempt
def api_preview_foto(request, jid):
    if request.method != 'GET': return JsonResponse({'success': False})
    try:
        w = resolve_jid_orm(jid); real_jid = w.id if w else jid
        
        logger.info(f"🎨 Iniciando generación de imagen para mundo: {w.name if w else jid}")
        b64 = GenerateWorldMapUseCase(DjangoCaosRepository(), StableDiffusionService()).generate_preview(real_jid)
        
        if b64 is None:
            logger.error("❌ generate_preview devolvió None - Revisa los logs de los servicios de IA")
            return JsonResponse({
                'status': 'error', 
                'success': False,
                'message': 'Error al generar la imagen. Verifica que los servidores de IA estén corriendo correctamente (Qwen en puerto 5000 y Stable Diffusion en puerto 7861).'
            })
        
        logger.info(f"✅ Imagen generada correctamente ({len(b64)} chars)")
        return JsonResponse({'status': 'ok', 'success': True, 'image': b64})
    except Exception as e:
        logger.error(f"❌ Exception en api_preview_foto: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'success': False, 'message': str(e)})

@csrf_exempt
def api_save_foto(request, jid):
    logger.debug(f"api_save_foto called for jid={jid}")
    try:
        w = resolve_jid_orm(jid); real_jid = w.id if w else jid
        
        data = json.loads(request.body)
        user = request.user if request.user.is_authenticated else None
        
        # Robust base64 decoding
        img_str = data.get('image')
        if not img_str:
            return JsonResponse({'status': 'error', 'message': 'No image data'})
            
        if ';base64,' in img_str:
            format, imgstr = img_str.split(';base64,') 
        else:
            imgstr = img_str

        # Convert to WebP
        image = Image.open(io.BytesIO(base64.b64decode(imgstr)))
        
        output = io.BytesIO()
        image.save(output, format='WEBP')
        
        file_name = f"{data.get('title')}.webp"
        image_data = ContentFile(output.getvalue(), name=file_name)

        # Determine period
        from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriod
        period_slug = data.get('period')
        period = TimelinePeriod.objects.filter(world=w, slug=period_slug).first()

        # Create Proposal
        CaosImageProposalORM.objects.create(
            world=w,
            image=image_data,
            title=data.get('title'),
            author=user,
            status='PENDING',
            action='ADD',
            timeline_period=period
        )
        
        log_event(request.user, "PROPOSE_AI_PHOTO", real_jid, f"Title: {data.get('title')}")
        
        return JsonResponse({'status': 'ok', 'success': True, 'message': 'Imagen enviada a revisión (WebP).'})
    except Exception as e:
        logger.error(f"Exception in api_save_foto: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def api_update_image_metadata(request, jid):
    try:
        w = resolve_jid_orm(jid); real_jid = w.id if w else jid
        data = json.loads(request.body)
        repo = DjangoCaosRepository()
        if hasattr(repo, 'update_image_metadata'):
            repo.update_image_metadata(real_jid, data.get('filename'), data.get('title'))
            return JsonResponse({'status': 'ok', 'success': True})
        return JsonResponse({'status': 'error', 'message': 'Repo method missing'})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

def subir_imagen_manual(request, jid):
    w = resolve_jid_orm(jid)
    real_jid = w.id if w else jid
    redirect_target = jid 
    if w and w.public_id: redirect_target = w.public_id

    if request.method == 'POST' and request.FILES.getlist('imagen_manual'):
        try:
            use_orig = request.POST.get('use_original_name') == 'true' or request.POST.get('use_original_name') == 'on'
            custom_base = request.POST.get('custom_name')
            title_base = request.POST.get('manual_title', 'Sin Título')
            
            files = request.FILES.getlist('imagen_manual')[:5] # Max 5
            
            # PERIOD SUPPORT
            from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriod
            period_slug = request.POST.get('period')
            period_obj = TimelinePeriod.objects.filter(world=w, slug=period_slug).first()
            
            for i, f in enumerate(files):
                final = title_base
                if len(files) > 1: final = f"{title_base} ({i+1})"
                
                if use_orig: final = f.name.split('.')[0]
                elif custom_base: 
                    final = custom_base
                    if len(files) > 1: final = f"{custom_base}_{i+1}"

                # --- SECURITY CHECK ---
                from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
                try: check_ownership(request.user, w)
                except: 
                    messages.error(request, "⛔ Solo el dueño puede subir imágenes.")
                    return redirect('ver_mundo', public_id=redirect_target)
                # ----------------------

                # --- PROPOSAL SAVE ---
                try:
                    from src.Infrastructure.DjangoFramework.persistence.models import CaosImageProposalORM
                    CaosImageProposalORM.objects.create(
                        world=w,
                        image=f,
                        title=final,
                        author=request.user if request.user.is_authenticated else None,
                        status='PENDING',
                        action='ADD',
                        timeline_period=period_obj
                    )
                    messages.success(request, f"📩 Propuesta para '{final}' enviada a revisión.")
                    log_event(request.user, "PROPOSE_MANUAL_PHOTO", real_jid, f"Manual Proposal: {final} (Period: {period_slug})")
                except Exception as e:
                     messages.error(request, f"Error al proponer imagen: {e}")
            
        except Exception as e: messages.error(request, f"Error: {e}")
    return redirect('ver_mundo', public_id=redirect_target)

def set_cover_image(request, jid, filename):
    try:
        w = resolve_jid_orm(jid)
        real_jid = w.id if w else jid
        
        # --- SECURITY CHECK ---
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        try: check_ownership(request.user, w)
        except: 
            messages.error(request, "⛔ Solo el dueño puede cambiar la portada.")
            return redirect('ver_mundo', public_id=jid)
        # ----------------------
        
        # Calculate next version
        next_v = CaosVersionORM.objects.filter(world=w).count() + 1
        
        CaosVersionORM.objects.create(
            world=w,
            proposed_name=w.name,
            proposed_description=w.description,
            version_number=next_v,
            status='PENDING',
            change_log=f"Propuesta de Portada: {filename}",
            cambios={'action': 'SET_COVER', 'cover_image': filename},
            author=request.user if request.user.is_authenticated else None
        )
        
        log_event(request.user, "PROPOSE_COVER", real_jid, f"Proposed cover: {filename}")
        messages.success(request, "📸 Propuesta de portada creada. Revisa el Dashboard.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error proponiendo portada: {e}")
        return redirect('ver_mundo', public_id=jid)

def borrar_foto(request, jid, filename):
    try: 
        w = resolve_jid_orm(jid)
        real_jid = w.id if w else jid
        
        # --- SECURITY CHECK ---
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        try: check_ownership(request.user, w)
        except: 
            messages.error(request, "⛔ No tienes permiso para borrar esta imagen.")
            return redirect('ver_mundo', public_id=w.public_id if w.public_id else w.id)
        # ----------------------
        
        # PERIOD SUPPORT
        from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriod
        period_slug = request.GET.get('period')
        period = TimelinePeriod.objects.filter(world=w, slug=period_slug).first()

        # Create Deletion Proposal
        CaosImageProposalORM.objects.create(
            world=w,
            title=f"Borrar: {filename}",
            reason=request.GET.get('reason', ''),
            target_filename=filename,
            action='DELETE',
            status='PENDING',
            author=request.user if request.user.is_authenticated else None,
            timeline_period=period
        )
        
        messages.info(request, "🗑️ Borrado pendiente de aprobación.")
        return redirect('ver_mundo', public_id=w.public_id if w.public_id else w.id)
    except Exception as e:
        logger.error(f"Error borrar_foto: {e}", exc_info=True)
        return redirect('home')

def generar_foto_extra(request, jid):
    return redirect('ver_mundo', public_id=jid)

def borrar_fotos_batch(request, jid):
    from django.http import JsonResponse
    import json
    
    if request.method != 'POST': 
        return JsonResponse({'status':'error', 'message':'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        filenames = data.get('filenames', [])
        reason = data.get('reason', '')
        
        if not filenames:
             return JsonResponse({'status':'error', 'message':'No has seleccionado ninguna foto.'})
             
        if len(filenames) > 5:
            return JsonResponse({'status':'error', 'message':'Máximo 5 fotos por lote.'})
            
        if not reason.strip():
             return JsonResponse({'status':'error', 'message':'El motivo es obligatorio.'})

        w = resolve_jid_orm(jid)
        if not w:
             return JsonResponse({'status':'error', 'message':'Mundo no encontrado'})

        # Security Check
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        try: check_ownership(request.user, w)
        except: return JsonResponse({'status':'error', 'message':'Permiso denegado'})

        # PERIOD SUPPORT
        from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriod
        period_slug = data.get('period')
        period = TimelinePeriod.objects.filter(world=w, slug=period_slug).first()

        count = 0
        for fn in filenames:
             CaosImageProposalORM.objects.create(
                 world=w,
                 title=f"Borrar: {fn}", 
                 reason=reason,
                 target_filename=fn,
                 action='DELETE',
                 status='PENDING',
                 author=request.user if request.user.is_authenticated else None,
                 timeline_period=period
             )
             count += 1
        
        messages.info(request, f"🗑️ Solicitado el borrado de {count} imágenes. Pendiente de aprobación.")
        return JsonResponse({'status':'ok'})
            
    except Exception as e:
        logger.error(f"Error batch delete: {e}", exc_info=True)
        return JsonResponse({'status':'error', 'message':str(e)})