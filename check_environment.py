"""
Environment Validation Script
Verifica que todas las variables de entorno necesarias estén configuradas.
"""
import os
import sys
from pathlib import Path

# Colores para output
class Colors:
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Variables requeridas
REQUIRED_VARS = [
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'DB_HOST',
    'DB_PORT',
    'SECRET_KEY',
]

# Variables opcionales pero recomendadas
OPTIONAL_VARS = [
    'DEBUG',
    'ALLOWED_HOSTS',
    'EMAIL_HOST',
    'EMAIL_PORT',
]

def check_env_file():
    """Verifica que existe el archivo .env"""
    env_file = Path('.env')
    if not env_file.exists():
        print(f"{Colors.FAIL}❌ Archivo .env no encontrado{Colors.END}")
        print(f"{Colors.WARNING}💡 Crea un archivo .env basado en .env.example{Colors.END}")
        return False
    return True

def load_env():
    """Carga variables de entorno desde .env"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return True
    except ImportError:
        print(f"{Colors.WARNING}⚠️  python-dotenv no instalado{Colors.END}")
        print(f"{Colors.WARNING}💡 Instala con: pip install python-dotenv{Colors.END}")
        return False

def check_required_vars():
    """Verifica variables requeridas"""
    missing = []
    present = []
    
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            present.append(var)
    
    return present, missing

def check_optional_vars():
    """Verifica variables opcionales"""
    present = []
    missing = []
    
    for var in OPTIONAL_VARS:
        value = os.getenv(var)
        if value:
            present.append(var)
        else:
            missing.append(var)
    
    return present, missing

def validate_values():
    """Valida que los valores tengan sentido"""
    warnings = []
    
    # Check DEBUG
    debug = os.getenv('DEBUG', 'False')
    if debug.lower() in ['true', '1', 'yes']:
        warnings.append("DEBUG está en True (OK para desarrollo, NO para producción)")
    
    # Check SECRET_KEY
    secret_key = os.getenv('SECRET_KEY', '')
    if len(secret_key) < 50:
        warnings.append("SECRET_KEY es muy corta (mínimo 50 caracteres recomendado)")
    
    # Check DB_PORT
    db_port = os.getenv('DB_PORT', '5432')
    if not db_port.isdigit():
        warnings.append(f"DB_PORT '{db_port}' no es un número válido")
    
    return warnings

def main():
    """Función principal"""
    print(f"{Colors.BOLD}{'='*60}")
    print("🔐 VERIFICACIÓN DE ENTORNO")
    print(f"{'='*60}{Colors.END}\n")
    
    # 1. Verificar archivo .env
    if not check_env_file():
        sys.exit(1)
    
    # 2. Cargar variables
    if not load_env():
        print(f"{Colors.WARNING}⚠️  Continuando sin cargar .env...{Colors.END}\n")
    
    # 3. Verificar variables requeridas
    present_req, missing_req = check_required_vars()
    
    print(f"{Colors.BOLD}Variables Requeridas:{Colors.END}")
    for var in present_req:
        value = os.getenv(var)
        # Ocultar valores sensibles
        if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
            display_value = '*' * min(len(value), 20)
        else:
            display_value = value[:50] + '...' if len(value) > 50 else value
        print(f"  {Colors.OK}✅ {var:20} = {display_value}{Colors.END}")
    
    if missing_req:
        print(f"\n{Colors.FAIL}❌ Variables Faltantes:{Colors.END}")
        for var in missing_req:
            print(f"  {Colors.FAIL}  - {var}{Colors.END}")
    
    # 4. Verificar variables opcionales
    present_opt, missing_opt = check_optional_vars()
    
    if present_opt:
        print(f"\n{Colors.BOLD}Variables Opcionales Configuradas:{Colors.END}")
        for var in present_opt:
            value = os.getenv(var)
            print(f"  {Colors.OK}✅ {var:20} = {value}{Colors.END}")
    
    if missing_opt:
        print(f"\n{Colors.WARNING}⚠️  Variables Opcionales No Configuradas:{Colors.END}")
        for var in missing_opt:
            print(f"  {Colors.WARNING}  - {var}{Colors.END}")
    
    # 5. Validar valores
    warnings = validate_values()
    if warnings:
        print(f"\n{Colors.WARNING}⚠️  Advertencias:{Colors.END}")
        for warning in warnings:
            print(f"  {Colors.WARNING}  - {warning}{Colors.END}")
    
    # 6. Resultado final
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    if missing_req:
        print(f"{Colors.FAIL}❌ ENTORNO INCOMPLETO - Faltan {len(missing_req)} variables requeridas{Colors.END}")
        print(f"{Colors.FAIL}{'='*60}{Colors.END}")
        sys.exit(1)
    else:
        print(f"{Colors.OK}✅ ENTORNO VÁLIDO - Todas las variables requeridas configuradas{Colors.END}")
        if warnings:
            print(f"{Colors.WARNING}⚠️  Revisa las advertencias arriba{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}")
        sys.exit(0)

if __name__ == '__main__':
    main()
