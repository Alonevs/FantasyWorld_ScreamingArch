#!/usr/bin/env python
import os
import sys
from pathlib import Path

def main():
    # --- PARCHE DE ARQUITECTURA ---
    # Obtenemos la ruta de este archivo y subimos 3 niveles para encontrar la RAIZ del proyecto
    # (DjangoFramework -> Infrastructure -> src -> RAIZ)
    current_path = Path(__file__).resolve().parent
    project_root = current_path.parents[2]
    
    # Añadimos la raíz al path de Python para que pueda encontrar 'src'
    sys.path.append(str(project_root))
    # -----------------------------

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
