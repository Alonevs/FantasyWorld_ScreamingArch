import os
import json
import base64
import io
from PIL import Image
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.base import ContentFile

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosEventLog, CaosImageProposalORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService

def resolve_jid(identifier):
    try:
        return CaosWorldORM.objects.get(public_id=identifier)
    except CaosWorldORM.DoesNotExist:
        pass 
    try:
        return CaosWorldORM.objects.get(id=identifier)
    except CaosWorldORM.DoesNotExist:
        return None

def log_event(user, action, target_id, details=""):
    try:
        u = user if user.is_authenticated else None
        CaosEventLog.objects.create(user=u, action=action, target_id=target_id, details=details)
    except Exception as e: print(f"Log Error: {e}")

@csrf_exempt
def api_preview_foto(request, jid):
    if request.method != 'GET': return JsonResponse({'success': False})
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        b64 = GenerateWorldMapUseCase(DjangoCaosRepository(), StableDiffusionService()).generate_preview(real_jid)
        return JsonResponse({'status': 'ok', 'success': True, 'image': b64})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def api_save_foto(request, jid):
    print(f"DEBUG: api_save_foto called for jid={jid}")
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        print(f"DEBUG: Resolved world: {w}")
        
        data = json.loads(request.body)
        print("DEBUG: Request body loaded")
        
        user = request.user if request.user.is_authenticated else None
        print(f"DEBUG: User: {user}")
        
        # Robust base64 decoding
        img_str = data.get('image')
        if not img_str:
            print("DEBUG: No image data found")
            return JsonResponse({'status': 'error', 'message': 'No image data'})
            
        if ';base64,' in img_str:
            format, imgstr = img_str.split(';base64,') 
        else:
            imgstr = img_str
        
        print(f"DEBUG: Image string length: {len(imgstr)}")

        # Convert to WebP
        print("DEBUG: Decoding base64...")
        image = Image.open(io.BytesIO(base64.b64decode(imgstr)))
        print(f"DEBUG: Image opened: {image.format} {image.size}")
        
        output = io.BytesIO()
        image.save(output, format='WEBP')
        print("DEBUG: Image saved to WebP buffer")
        
        file_name = f"{data.get('title')}.webp"
        image_data = ContentFile(output.getvalue(), name=file_name)
        print(f"DEBUG: ContentFile created: {file_name}")

        # Create Proposal
        print("DEBUG: Creating CaosImageProposalORM...")
        CaosImageProposalORM.objects.create(
            world=w,
            image=image_data,
            title=data.get('title'),
            author=user,
            status='PENDING'
        )
        print("DEBUG: CaosImageProposalORM created")
        
        log_event(request.user, "PROPOSE_AI_PHOTO", real_jid, f"Title: {data.get('title')}")
        print("DEBUG: Event logged")
        
        return JsonResponse({'status': 'ok', 'success': True, 'message': 'Imagen enviada a revisión (WebP).'})
    except Exception as e:
        print(f"DEBUG: Exception in api_save_foto: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def api_update_image_metadata(request, jid):
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        data = json.loads(request.body)
        repo = DjangoCaosRepository()
        if hasattr(repo, 'update_image_metadata'):
            repo.update_image_metadata(real_jid, data.get('filename'), data.get('title'))
            return JsonResponse({'status': 'ok', 'success': True})
        return JsonResponse({'status': 'error', 'message': 'Repo method missing'})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

def subir_imagen_manual(request, jid):
    w = resolve_jid(jid)
    real_jid = w.id if w else jid
    redirect_target = jid 
    if w and w.public_id: redirect_target = w.public_id

    if request.method == 'POST' and request.FILES.getlist('imagen_manual'):
        try:
            use_orig = request.POST.get('use_original_name') == 'true' or request.POST.get('use_original_name') == 'on'
            custom_base = request.POST.get('custom_name')
            title_base = request.POST.get('manual_title', 'Sin Título')
            
            files = request.FILES.getlist('imagen_manual')[:5] # Max 5
            
            for i, f in enumerate(files):
                final = title_base
                if len(files) > 1: final = f"{title_base} ({i+1})"
                
                if use_orig: final = f.name.split('.')[0]
                elif custom_base: 
                    final = custom_base
                    if len(files) > 1: final = f"{custom_base}_{i+1}"

                user = request.user if request.user.is_authenticated else None
                # Create Proposal
                CaosImageProposalORM.objects.create(
                    world=w,
                    image=f,
                    title=final,
                    author=user,
                    status='PENDING'
                )
                log_event(request.user, "PROPOSE_PHOTO", real_jid, f"File: {final}")
            
            messages.success(request, f"✨ {len(files)} imagen(es) enviada(s) a revisión. Aprobar en Dashboard.")
        except Exception as e: messages.error(request, f"Error: {e}")
    return redirect('ver_mundo', public_id=redirect_target)

def set_cover_image(request, jid, filename):
    try: w=resolve_jid(jid); w.metadata['cover_image']=filename; w.save(); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')

def borrar_foto(request, jid, filename):
    try: 
        w=resolve_jid(jid); base=os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', w.id)
        if os.path.exists(os.path.join(base, filename)): 
            os.remove(os.path.join(base, filename))
            log_event(request.user, "DELETE_PHOTO", w.id, f"File: {filename}")
        return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')

def generar_foto_extra(request, jid):
    return redirect('ver_mundo', public_id=jid)