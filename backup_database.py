"""
Automated Database Backup Script
Crea backups diarios de la base de datos PostgreSQL con compresión y limpieza automática.
"""
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backups/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración
BACKUP_DIR = Path('backups/database')
RETENTION_DAYS = 30

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'fantasyworld_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def create_backup_dir():
    """Crea el directorio de backups si no existe"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directorio de backups: {BACKUP_DIR.absolute()}")

def backup_database():
    """Crea un backup de la base de datos PostgreSQL"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = BACKUP_DIR / f"db_{timestamp}.sql"
        
        logger.info(f"Iniciando backup de base de datos: {DB_NAME}")
        
        # Comando pg_dump
        cmd = [
            'pg_dump',
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-U', DB_USER,
            '-d', DB_NAME,
            '-f', str(filename),
            '--verbose'
        ]
        
        # Ejecutar backup
        env = os.environ.copy()
        env['PGPASSWORD'] = os.getenv('DB_PASSWORD', '')
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"✅ Backup creado: {filename}")
        
        # Comprimir con gzip
        logger.info("Comprimiendo backup...")
        subprocess.run(['gzip', str(filename)], check=True)
        compressed_file = f"{filename}.gz"
        
        # Obtener tamaño
        size_mb = Path(compressed_file).stat().st_size / (1024 * 1024)
        logger.info(f"✅ Backup comprimido: {compressed_file} ({size_mb:.2f} MB)")
        
        return compressed_file
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error al crear backup: {e}")
        logger.error(f"Output: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return None

def cleanup_old_backups():
    """Elimina backups más antiguos que RETENTION_DAYS"""
    try:
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        deleted_count = 0
        
        for backup_file in BACKUP_DIR.glob('db_*.sql.gz'):
            # Extraer fecha del nombre del archivo
            try:
                date_str = backup_file.stem.split('_')[1]  # db_YYYYMMDD_HHMMSS.sql
                file_date = datetime.strptime(date_str, '%Y%m%d')
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"🗑️  Eliminado backup antiguo: {backup_file.name}")
            except (ValueError, IndexError):
                logger.warning(f"⚠️  No se pudo parsear fecha de: {backup_file.name}")
        
        if deleted_count > 0:
            logger.info(f"✅ Limpieza completada: {deleted_count} backups eliminados")
        else:
            logger.info("✅ No hay backups antiguos para eliminar")
            
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")

def verify_backup(backup_file):
    """Verifica que el backup se puede descomprimir"""
    try:
        if not backup_file:
            return False
            
        result = subprocess.run(
            ['gzip', '-t', backup_file],
            capture_output=True,
            check=True
        )
        logger.info("✅ Backup verificado correctamente")
        return True
    except subprocess.CalledProcessError:
        logger.error("❌ Backup corrupto!")
        return False

def main():
    """Función principal"""
    logger.info("="*60)
    logger.info("INICIANDO BACKUP AUTOMÁTICO DE BASE DE DATOS")
    logger.info("="*60)
    
    # Crear directorio
    create_backup_dir()
    
    # Crear backup
    backup_file = backup_database()
    
    if backup_file:
        # Verificar backup
        if verify_backup(backup_file):
            # Limpiar backups antiguos
            cleanup_old_backups()
            logger.info("="*60)
            logger.info("✅ BACKUP COMPLETADO EXITOSAMENTE")
            logger.info("="*60)
            return 0
        else:
            logger.error("="*60)
            logger.error("❌ BACKUP FALLÓ - ARCHIVO CORRUPTO")
            logger.error("="*60)
            return 1
    else:
        logger.error("="*60)
        logger.error("❌ BACKUP FALLÓ")
        logger.error("="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
