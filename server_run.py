import subprocess
import os
import sys

def main():
    # Path to manage.py relative to project root
    manage_py_path = os.path.join("src", "Infrastructure", "DjangoFramework", "manage.py")
    
    if not os.path.exists(manage_py_path):
        print(f"Error: Could not find {manage_py_path}")
        sys.exit(1)
        
    print("Iniciando el servidor de Django...")
    
    # Auto-detect virtualenv python
    python_exe = sys.executable
    if os.name == 'nt': # Windows
        venv_python = os.path.join("venv", "Scripts", "python.exe")
    else: # Unix
        venv_python = os.path.join("venv", "bin", "python")
        
    if os.path.exists(venv_python):
        python_exe = venv_python
        print(f"🐍 Usando entorno virtual: {venv_python}")

    # Run migrations
    try:
        print("🔄 Verificando migraciones de base de datos...")
        subprocess.run([python_exe, manage_py_path, "makemigrations"], check=True)
        subprocess.run([python_exe, manage_py_path, "migrate"], check=True)
    except Exception as e:
        print(f"⚠️ Error en migraciones (continuando...): {e}")

    # Run the server
    try:
        subprocess.run([python_exe, manage_py_path, "runserver"], check=True)
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
