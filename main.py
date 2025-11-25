import sys
import os
import django
import time

# --- 1. SETUP DE ARQUITECTURA (Para que Python encuentre tus carpetas) ---
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

print("✅ Django inicializado correctamente. Conectando con db.sqlite3...\n")

# --- 2. IMPORTS ---
# Repositorios y Dominio
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.publish_world import PublishWorldUseCase

# Servicios de IA
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService

# Casos de Uso de IA
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase

def main():
    print("=== FANTASY WORLD GENERATOR v3.0 (TEXT + IMAGE) ===\n")
    
    # 1. Instanciar Repositorio (Memoria de Django)
    repo = DjangoCaosRepository()
    
    # 2. Conectar Cerebro (Llama 3 / Oobabooga)
    try:
        ia_texto = Llama3Service()
        print(" 🧠 Servicio de Texto: ACTIVO")
    except Exception as e:
        print(f" ⚠️ Servicio de Texto: INACTIVO ({e})")
        ia_texto = None
    
    # 3. Conectar Pintor (Stable Diffusion / Automatic1111)
    try:
        ia_arte = StableDiffusionService()
        print(" 🎨 Servicio de Arte: ACTIVO")
    except Exception as e:
        print(f" ⚠️ Servicio de Arte: INACTIVO ({e})")
        ia_arte = None

    # 4. Preparar Casos de Uso (Las herramientas)
    crear = CreateWorldUseCase(repo)
    publicar = PublishWorldUseCase(repo)
    gen_lore = GenerateWorldLoreUseCase(repo, ia_texto) if ia_texto else None
    gen_mapa = GenerateWorldMapUseCase(repo, ia_arte) if ia_arte else None

    print("\n------------------------------------------------")

    try:
        # --- PASO 1: CREAR MUNDO (Estructura Base) ---
        print("🔹 1. Creando Entidad 'Azeroth'...")
        # Esto nos devuelve el J-ID puro ("01")
        world_jid = crear.execute("Azeroth", "Mundo base generado por CLI")
        
        # --- PASO 2: GENERAR LORE (Historia) ---
        if gen_lore:
            print("\n🔹 2. Escribiendo Historia (Llama 3)...")
            gen_lore.execute(world_jid)
        else:
            print("\n🔸 Saltando historia (IA de texto no disponible)")
        
        # --- PASO 3: GENERAR ARTE (Imagen) ---
        if gen_mapa:
            print("\n🔹 3. Pintando Retrato (Stable Diffusion)...")
            print("    (Esto puede tardar unos segundos...)")
            # Pequeña pausa para no saturar si corres todo muy rápido
            time.sleep(1)
            gen_mapa.execute(world_jid)
        else:
            print("\n🔸 Saltando imagen (IA de arte no disponible)")

        # --- PASO 4: PUBLICAR (Hacerlo oficial) ---
        print("\n🔹 4. Publicando Mundo...")
        publicar.execute(world_jid)

    except Exception as e:
        print(f"\n❌ Error Crítico en el proceso: {e}")

    print("\n================================================")
    print("🚀 PROCESO TERMINADO.")
    print("👉 Para ver el resultado: python src/Infrastructure/DjangoFramework/manage.py runserver")

if __name__ == "__main__":
    main()