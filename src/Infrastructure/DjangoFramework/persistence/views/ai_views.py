from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, MetadataTemplate, CaosNarrativeORM
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository

@login_required
@require_POST
def analyze_metadata_api(request):
    try:
        data = json.loads(request.body)
        world_id_raw = data.get('world_id')
        
        print(f"🔍 DEBUG AI: Recibido world_id raw: {world_id_raw}")
        
        if not world_id_raw:
             return JsonResponse({'success': False, 'error': 'Missing world_id'})

        # RESOLUCION DE MUNDO ROBUSTA (CASCADA)
        w_orm = None
        
        # 1. Intentar por ID exacto (PK es String en CaosWorldORM)
        if not w_orm:
            try:
                w_orm = CaosWorldORM.objects.get(id=world_id_raw)
                print(f"✅ DEBUG AI: Mundo encontrado por ID exacto: '{world_id_raw}'")
            except CaosWorldORM.DoesNotExist:
                pass
        
        # 2. Intentar por public_id (NanoID)
        if not w_orm:
            try:
                w_orm = CaosWorldORM.objects.get(public_id=world_id_raw)
                print(f"✅ DEBUG AI: Mundo encontrado por Public ID: '{world_id_raw}'")
            except (CaosWorldORM.DoesNotExist, Exception):
                pass

        # 3. Intentar por id_codificado (Campo Jerárquico, ej: "01")
        if not w_orm:
            try:
                w_orm = CaosWorldORM.objects.get(id_codificado=world_id_raw)
                print(f"✅ DEBUG AI: Mundo encontrado por id_codificado: '{world_id_raw}'")
            except (CaosWorldORM.DoesNotExist, Exception):
                pass
                
        if not w_orm:
             print(f"❌ DEBUG AI: Fallaron todas las búsquedas (ID, PublicID, J-ID) para: {world_id_raw}")
             return JsonResponse({'success': False, 'error': f'World not found for {world_id_raw}'})

        print(f"✅ DEBUG AI: Mundo resuelto: {w_orm.name} (ID: {w_orm.id})")
        
        # OBTENCION DE TEXTO (Cascada)
        texto_final = ""
        
        # Buscar Narrativas (LORE o ROOT)
        narrativas = CaosNarrativeORM.objects.filter(world_id=w_orm.id)
        
        # Prioridad 1: Tipo LORE
        lore_real = narrativas.filter(tipo='LORE').order_by('-created_at').first()
        
        # Prioridad 2: Tipo ROOT (si no hay LORE)
        if not lore_real:
            lore_real = narrativas.filter(tipo='ROOT').first()
            
        # Prioridad 3: Cualquier cosa que NO sea "Nuevo Documento" (ignora basura)
        if not lore_real:
            lore_real = narrativas.exclude(titulo__icontains="Nuevo Documento").order_by('-created_at').first()

        if lore_real and lore_real.contenido:
            print(f"✅ DEBUG AI: Usando Narrativa '{lore_real.titulo}' (Tipo: {lore_real.tipo})")
            texto_final = f"{lore_real.titulo}:\n{lore_real.contenido}"
        else:
            print("DEBUG: Usando Descripción de Mundo (Fallback)")
            texto_final = w_orm.description or ""
            
        if not texto_final.strip():
             texto_final = f"Mundo: {w_orm.name}. No hay datos disponibles."
             
        print(f"🔍 DEBUG AI: Texto enviado ({len(texto_final)} chars): {texto_final[:100]}...")
        
        # Call AI
        # Ignoring template schema as per Open Extraction req
        service = Llama3Service()
        extracted_data = service.extract_metadata(texto_final)
        
        if not extracted_data:
             return JsonResponse({
                 'success': False, 
                 'error': 'AI returned empty data. Check server console for "LlamaService" logs.',
                 'debug_info': 'Connection to Port 5000 failed or JSON parse error.'
             })
        
        return JsonResponse({
            'success': True,
            'metadata': extracted_data
        })

    except Exception as e:
        print(f"AI API Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
