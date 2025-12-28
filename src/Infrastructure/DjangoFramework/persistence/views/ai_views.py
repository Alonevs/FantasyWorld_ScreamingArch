from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, MetadataTemplate, CaosNarrativeORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.FantasyWorld.Domain.Services.NarrativeService import NarrativeService
from .view_utils import resolve_jid_orm

@login_required
@require_POST
def analyze_metadata_api(request):
    try:
        data = json.loads(request.body)
        world_id_raw = data.get('world_id')
        

        
        if not world_id_raw:
            return JsonResponse({'success': False, 'error': 'Missing world_id'})
        
        # EXTRACCIÓN DEL MUNDO DESDE NID (si es narrativa)
        # Formato NID: 0101L01, 01C03, etc. -> Extraer prefijo del mundo (0101, 01)
        world_code = world_id_raw
        if any(marker in world_id_raw for marker in ['L', 'C', 'H', 'E', 'R', 'B']):
            # Es un NID, extraer el prefijo del mundo (antes del marcador)
            for marker in ['L', 'C', 'H', 'E', 'R', 'B']:
                if marker in world_id_raw:
                    world_code = world_id_raw.split(marker)[0]
                    break


        # RESOLUCION DE MUNDO POR ID (Jerárquico o Público)
        w_orm = resolve_jid_orm(world_code)
                
        if not w_orm:
            # Try original raw ID in case it's a NanoID not matched by the code extractor
            w_orm = resolve_jid_orm(world_id_raw)

        if not w_orm:
            return JsonResponse({
                'success': False, 
                'error': f'❌ Mundo no encontrado para: {world_id_raw}'
            })

        
        # OBTENCION DE TEXTO (Cascada)
        texto_final = ""
        
        # Buscar Narrativas LORE específicamente para este mundo
        narrativas = CaosNarrativeORM.objects.filter(world=w_orm)
        
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
            # NO HAY LORE - Permitir Cold Start (Metadata Placeholder)
            texto_final = ""
            
        if not texto_final.strip():
            texto_final = f"Mundo: {w_orm.name}. No hay datos disponibles."
             

        
        # Call AI
        # Call AI via Use Case (V2 Logic - Schemas + Cold Start)
        service = Llama3Service()
        repo = DjangoCaosRepository()
        
        # Local import to avoid circular dependency
        from src.WorldManagement.Caos.Application.generate_contextual_metadata import GenerateContextualMetadataUseCase
        
        use_case = GenerateContextualMetadataUseCase(repo, service)
        extracted_data = use_case.execute(w_orm.id)
        if not extracted_data:
            return JsonResponse({
                'success': False, 
                'error': 'AI returned empty data. Check server console for "LlamaService" logs.',
                'debug_info': 'Connection to AI Service failed or JSON parse error.'
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
        world_id = data.get('world_id', None)  # NUEVO: Para contexto jerárquico

        # Length Validation (approx 6-7 pages max to avoid timeout/context overflow)
        if len(text.split()) > 4000:
            return JsonResponse({'success': False, 'error': 'Texto demasiado largo (Máx ~4000 palabras). Por favor, edita por partes.'})

        # NUEVO: Build hierarchical context
        from src.FantasyWorld.Domain.Services.ContextService import ContextBuilder
        context_prompt = ""
        if world_id:
            context_prompt = ContextBuilder.build_hierarchy_context(world_id)

        # Dynamic Prompts
        prompts = {
            'fix': "Eres un Editor Corrector. Corrige ortografía, gramática y puntuación del siguiente texto. NO cambies el estilo ni el contenido. Devuelve SOLO el texto corregido, sin introducciones.",
            'enrich': "Eres un Novelista Experto. Enriquece el vocabulario y las descripciones del siguiente texto para hacerlo más inmersivo y literario. Mantén la trama original. Devuelve SOLO el texto mejorado, sin introducciones.",
            'format': "Eres un Maquetador. Aplica formato Markdown al siguiente texto: Usa '##' para títulos de capítulos, '**' para énfasis y '-' para listas si hay enumeraciones. Arregla los saltos de línea para que los párrafos se vean bien. Devuelve SOLO el texto formateado."
        }
        
        system_prompt = prompts.get(mode, prompts['fix'])
        
        # NUEVO: Inject context if available
        if context_prompt:
            system_prompt += f"\n{context_prompt}\nRESPETA las reglas y el contexto de la jerarquía al editar."
        
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
        world_id = data.get('world_id', None)  # Optional: para contexto jerárquico

        clean_title = NarrativeService.generate_magic_title(text, world_id=world_id)

        return JsonResponse({'success': True, 'title': clean_title})
    except Exception as e:
        print(f"❌ ERROR API TITLE: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_POST
def api_generate_lore(request):
    """Genera lore creativo basado en el nombre y contexto del mundo."""
    try:
        data = json.loads(request.body)
        world_id = data.get('world_id')
        current_description = data.get('current_description', '') # Capture user context
        
        if not world_id:
            return JsonResponse({'success': False, 'error': 'Missing world_id'})

        repo = DjangoCaosRepository()
        service = Llama3Service()
        
        from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
        use_case = GenerateWorldLoreUseCase(repo, service)
        
        # Execute with Context and Preview Mode (Do NOT save to DB yet)
        lore_text = use_case.execute(world_id, current_context=current_description, preview_mode=True)
        
        if lore_text:
            return JsonResponse({'success': True, 'lore': lore_text})
        else:
            return JsonResponse({'success': False, 'error': 'La IA no pudo generar el lore.'})

    except Exception as e:
        print(f"❌ ERROR LORE GEN: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
