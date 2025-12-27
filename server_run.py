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
    
    # Run the server
    try:
        subprocess.run([sys.executable, manage_py_path, "runserver"], check=True)
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
