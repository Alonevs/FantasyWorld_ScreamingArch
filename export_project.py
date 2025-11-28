import os
from datetime import datetime

# --- CONFIGURACIÓN ---
OUTPUT_FILE = "PROJECT_CONTEXT.txt"
ROOT_DIR = "."  # Directorio actual

# Extensiones que nos interesan (Código y Documentación)
INCLUDED_EXTENSIONS = {
    '.py', '.html', '.css', '.js', '.md', '.txt'
}

# Carpetas a ignorar (Basura, entornos virtuales, caches)
IGNORE_DIRS = {
    'venv', 'env', '.git', '__pycache__', '.pytest_cache', 
    'migrations', 'static', 'media', 'img', 'assets', 
    '.idea', '.vscode'
}

# Archivos específicos a ignorar
IGNORE_FILES = {
    'db.sqlite3', 'poetry.lock', 'package-lock.json', 
    OUTPUT_FILE, 'export_project.py', 'dev_context_exporter.py'
}

def get_tree_structure(startpath):
    """Genera un mapa visual del árbol de carpetas"""
    tree_str = "📦 ESTRUCTURA DEL PROYECTO:\n"
    for root, dirs, files in os.walk(startpath):
        # Filtrar directorios in-situ para no entrar en ellos
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree_str += '{}{}/\n'.format(indent, os.path.basename(root))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f not in IGNORE_FILES and os.path.splitext(f)[1] in INCLUDED_EXTENSIONS:
                tree_str += '{}{}\n'.format(subindent, f)
    return tree_str

def main():
    print(f"🚀 Escaneando proyecto en: {os.path.abspath(ROOT_DIR)}")
    start_time = datetime.now()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        # 1. Cabecera con Timestamp
        outfile.write(f"PROJECT SNAPSHOT: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        outfile.write("="*60 + "\n\n")

        # 2. Mapa del Proyecto
        outfile.write(get_tree_structure(ROOT_DIR))
        outfile.write("\n" + "="*60 + "\n\n")

        # 3. Contenido de los Archivos
        file_count = 0
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                if file in IGNORE_FILES: continue
                
                ext = os.path.splitext(file)[1]
                if ext in INCLUDED_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    
                    # Separador claro para que la IA distinga archivos
                    header = f"\n{'='*20} FILE: {file_path} {'='*20}\n"
                    outfile.write(header)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                            file_count += 1
                    except Exception as e:
                        outfile.write(f"Error leyendo archivo: {e}\n")
                    
                    outfile.write("\n")

    print(f"✅ ¡Listo! {file_count} archivos exportados a '{OUTPUT_FILE}'.")
    print(f"👉 Sube este archivo al nuevo chat.")

if __name__ == "__main__":
    main()