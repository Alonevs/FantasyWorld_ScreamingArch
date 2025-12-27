# Backup Scripts - FantasyWorld

## 📋 Scripts Disponibles

### 1. backup_database.py
Crea backups automáticos de la base de datos PostgreSQL.

**Características:**
- Backup completo de la BD
- Compresión con gzip
- Retención de 30 días
- Verificación de integridad
- Logging detallado

**Uso:**
```bash
python backup_database.py
```

**Requisitos:**
- PostgreSQL instalado
- `pg_dump` en PATH
- Variables en `.env`: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

### 2. backup_media.py
Crea backups automáticos de archivos de medios (imágenes).

**Características:**
- Copia completa de `/static/persistence/img/`
- Retención de 30 días
- Verificación de archivos
- Logging detallado

**Uso:**
```bash
python backup_media.py
```

---

## 🔧 Configuración

### Crear Directorios
Los scripts crean automáticamente:
- `backups/database/` - Backups de BD
- `backups/media/` - Backups de medios
- `backups/backup.log` - Log de operaciones

### Variables de Entorno (.env)
```env
DB_NAME=fantasyworld_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

---

## ⏰ Automatización

### Windows - Task Scheduler

#### Backup Diario de Base de Datos (3 AM)
```powershell
schtasks /create /tn "FantasyWorld_DB_Backup" /tr "python C:\path\to\backup_database.py" /sc daily /st 03:00 /ru SYSTEM
```

#### Backup Diario de Medios (3:15 AM)
```powershell
schtasks /create /tn "FantasyWorld_Media_Backup" /tr "python C:\path\to\backup_media.py" /sc daily /st 03:15 /ru SYSTEM
```

#### Verificar Tareas
```powershell
schtasks /query /tn "FantasyWorld_DB_Backup"
schtasks /query /tn "FantasyWorld_Media_Backup"
```

#### Ejecutar Manualmente
```powershell
schtasks /run /tn "FantasyWorld_DB_Backup"
schtasks /run /tn "FantasyWorld_Media_Backup"
```

#### Eliminar Tareas
```powershell
schtasks /delete /tn "FantasyWorld_DB_Backup" /f
schtasks /delete /tn "FantasyWorld_Media_Backup" /f
```

### Linux/Mac - Crontab

```bash
# Editar crontab
crontab -e

# Agregar líneas:
0 3 * * * cd /path/to/project && python backup_database.py
15 3 * * * cd /path/to/project && python backup_media.py
```

---

## 🔄 Restauración

### Restaurar Base de Datos
```bash
# 1. Descomprimir
gunzip backups/database/db_20250127_030000.sql.gz

# 2. Restaurar
psql -U postgres -d fantasyworld_db < backups/database/db_20250127_030000.sql
```

### Restaurar Medios
```bash
# Copiar backup a directorio de medios
xcopy backups\media\20250127 src\Infrastructure\DjangoFramework\persistence\static\persistence\img /E /I /Y
```

---

## 📊 Monitoreo

### Ver Logs
```bash
type backups\backup.log
```

### Verificar Backups Recientes
```bash
# Base de datos
dir backups\database /O-D

# Medios
dir backups\media /O-D
```

### Tamaño de Backups
```powershell
# Total de backups de BD
Get-ChildItem backups\database -Recurse | Measure-Object -Property Length -Sum

# Total de backups de medios
Get-ChildItem backups\media -Recurse | Measure-Object -Property Length -Sum
```

---

## ⚠️ Notas Importantes

1. **Espacio en Disco**: Los backups consumen espacio. Monitorear regularmente.
2. **Retención**: Por defecto 30 días. Ajustar `RETENTION_DAYS` si necesario.
3. **Permisos**: Asegurar que el usuario tiene permisos de escritura en `backups/`.
4. **Testing**: Probar restauración al menos una vez al mes.
5. **Nube**: Para producción, considerar sync a S3/Supabase.

---

## 🚨 Troubleshooting

### Error: "pg_dump not found"
- Agregar PostgreSQL bin a PATH
- Windows: `C:\Program Files\PostgreSQL\15\bin`

### Error: "Permission denied"
- Ejecutar como administrador
- Verificar permisos de carpeta `backups/`

### Backup muy grande
- Considerar backups incrementales
- Comprimir medios con mayor ratio
- Reducir retención de días

---

## 📈 Próximos Pasos

1. ✅ Implementar scripts locales
2. ⏰ Configurar Task Scheduler
3. 🧪 Probar restauración
4. ☁️ Configurar sync a nube (producción)
5. 📧 Agregar alertas por email si falla
