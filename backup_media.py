"""
Automated Media Backup Script
Crea backups diarios de archivos de medios (imágenes) con limpieza automática.
"""
import os
import shutil
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
MEDIA_DIR = Path('src/Infrastructure/DjangoFramework/persistence/static/persistence/img')
BACKUP_DIR = Path('backups/media')
RETENTION_DAYS = 30

def create_backup_dir():
    """Crea el directorio de backups si no existe"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directorio de backups: {BACKUP_DIR.absolute()}")

def get_directory_size(path):
    """Calcula el tamaño total de un directorio"""
    total = 0
    for entry in Path(path).rglob('*'):
        if entry.is_file():
            total += entry.stat().st_size
    return total

def backup_media():
    """Crea un backup de los archivos de medios"""
    try:
        if not MEDIA_DIR.exists():
            logger.warning(f"⚠️  Directorio de medios no existe: {MEDIA_DIR}")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d')
        dest_dir = BACKUP_DIR / timestamp
        
        # Verificar si ya existe backup de hoy
        if dest_dir.exists():
            logger.warning(f"⚠️  Backup de hoy ya existe: {dest_dir}")
            logger.info("Eliminando backup existente para recrear...")
            shutil.rmtree(dest_dir)
        
        logger.info(f"Iniciando backup de medios desde: {MEDIA_DIR}")
        logger.info(f"Destino: {dest_dir}")
        
        # Copiar directorio completo
        shutil.copytree(MEDIA_DIR, dest_dir)
        
        # Calcular tamaño
        size_mb = get_directory_size(dest_dir) / (1024 * 1024)
        file_count = sum(1 for _ in dest_dir.rglob('*') if _.is_file())
        
        logger.info(f"✅ Backup de medios creado: {dest_dir}")
        logger.info(f"   Archivos: {file_count}")
        logger.info(f"   Tamaño: {size_mb:.2f} MB")
        
        return dest_dir
        
    except Exception as e:
        logger.error(f"❌ Error al crear backup de medios: {e}")
        return None

def cleanup_old_backups():
    """Elimina backups más antiguos que RETENTION_DAYS"""
    try:
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        deleted_count = 0
        
        for backup_dir in BACKUP_DIR.iterdir():
            if not backup_dir.is_dir():
                continue
            
            try:
                # Parsear fecha del nombre (YYYYMMDD)
                date_str = backup_dir.name
                dir_date = datetime.strptime(date_str, '%Y%m%d')
                
                if dir_date < cutoff_date:
                    shutil.rmtree(backup_dir)
                    deleted_count += 1
                    logger.info(f"🗑️  Eliminado backup antiguo: {backup_dir.name}")
            except ValueError:
                logger.warning(f"⚠️  No se pudo parsear fecha de: {backup_dir.name}")
        
        if deleted_count > 0:
            logger.info(f"✅ Limpieza completada: {deleted_count} backups eliminados")
        else:
            logger.info("✅ No hay backups antiguos para eliminar")
            
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")

def verify_backup(backup_dir):
    """Verifica que el backup contiene archivos"""
    try:
        if not backup_dir or not backup_dir.exists():
            return False
        
        file_count = sum(1 for _ in backup_dir.rglob('*') if _.is_file())
        
        if file_count > 0:
            logger.info(f"✅ Backup verificado: {file_count} archivos")
            return True
        else:
            logger.error("❌ Backup vacío!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verificando backup: {e}")
        return False

def main():
    """Función principal"""
    logger.info("="*60)
    logger.info("INICIANDO BACKUP AUTOMÁTICO DE MEDIOS")
    logger.info("="*60)
    
    # Crear directorio
    create_backup_dir()
    
    # Crear backup
    backup_dir = backup_media()
    
    if backup_dir:
        # Verificar backup
        if verify_backup(backup_dir):
            # Limpiar backups antiguos
            cleanup_old_backups()
            logger.info("="*60)
            logger.info("✅ BACKUP DE MEDIOS COMPLETADO EXITOSAMENTE")
            logger.info("="*60)
            return 0
        else:
            logger.error("="*60)
            logger.error("❌ BACKUP DE MEDIOS FALLÓ - VERIFICACIÓN FALLIDA")
            logger.error("="*60)
            return 1
    else:
        logger.error("="*60)
        logger.error("❌ BACKUP DE MEDIOS FALLÓ")
        logger.error("="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
