from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, MetadataTemplate, CaosNarrativeORM
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.FantasyWorld.Domain.Services.NarrativeService import NarrativeService

@login_required
@require_POST
def analyze_metadata_api(request):
    try:
        data = json.loads(request.body)
        world_id_raw = data.get('world_id')
        

        
        if not world_id_raw:
            return JsonResponse({'success': False, 'error': 'Missing world_id'})

        # RESOLUCION DE MUNDO ROBUSTA (CASCADA)
        w_orm = None
        
        # 1. Intentar por ID exacto (PK es String en CaosWorldORM)
        if not w_orm:
            try:
                w_orm = CaosWorldORM.objects.get(id=world_id_raw)

            except CaosWorldORM.DoesNotExist:
                pass
        
        # 2. Intentar por public_id (NanoID)
        if not w_orm:
            try:
                w_orm = CaosWorldORM.objects.get(public_id=world_id_raw)

            except (CaosWorldORM.DoesNotExist, Exception):
                pass

        # 3. Intentar por id_codificado (Campo Jerárquico, ej: "01")
        if not w_orm:
            try:
                w_orm = CaosWorldORM.objects.get(id_codificado=world_id_raw)

            except (CaosWorldORM.DoesNotExist, Exception):
                pass
                
        if not w_orm:

            return JsonResponse({'success': False, 'error': f'World not found for {world_id_raw}'})


        
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

            texto_final = f"{lore_real.titulo}:\n{lore_real.contenido}"
        else:

            texto_final = w_orm.description or ""
            
        if not texto_final.strip():
            texto_final = f"Mundo: {w_orm.name}. No hay datos disponibles."
             

        
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

@csrf_exempt
@login_required
@require_POST
def edit_narrative_api(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        mode = data.get('mode', 'fix')

        # Length Validation (approx 6-7 pages max to avoid timeout/context overflow)
        if len(text.split()) > 4000:
            return JsonResponse({'success': False, 'error': 'Texto demasiado largo (Máx ~4000 palabras). Por favor, edita por partes.'})

        # Dynamic Prompts
        prompts = {
            'fix': "Eres un Editor Corrector. Corrige ortografía, gramática y puntuación del siguiente texto. NO cambies el estilo ni el contenido. Devuelve SOLO el texto corregido, sin introducciones.",
            'enrich': "Eres un Novelista Experto. Enriquece el vocabulario y las descripciones del siguiente texto para hacerlo más inmersivo y literario. Mantén la trama original. Devuelve SOLO el texto mejorado, sin introducciones.",
            'format': "Eres un Maquetador. Aplica formato Markdown al siguiente texto: Usa '##' para títulos de capítulos, '**' para énfasis y '-' para listas si hay enumeraciones. Arregla los saltos de línea para que los párrafos se vean bien. Devuelve SOLO el texto formateado."
        }
        
        system_prompt = prompts.get(mode, prompts['fix'])
        
        service = Llama3Service()
        result_text = service.edit_text(system_prompt, text)
        
        if not result_text:
            return JsonResponse({'success': False, 'error': 'La IA no devolvió respuesta. Intenta con un texto más corto.'})

        return JsonResponse({'success': True, 'text': result_text})

    except Exception as e:
        print(f"❌ ERROR API IA: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_POST
def api_generate_title(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')

        clean_title = NarrativeService.generate_magic_title(text)

        return JsonResponse({'success': True, 'title': clean_title})

    except Exception as e:
        print(f"❌ ERROR API TITLE: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
