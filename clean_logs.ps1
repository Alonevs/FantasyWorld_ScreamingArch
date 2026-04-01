# Script para limpiar logs antiguos y grandes
# Ejecutar manualmente cuando sea necesario

Write-Host "🧹 Limpiando archivos de log antiguos..." -ForegroundColor Cyan

# Archivos de log en la raíz del proyecto
$rootLogs = @(
    "error.log",
    "errores_django.log",
    "security_audit.log",
    "verification.log"
)

foreach ($log in $rootLogs) {
    if (Test-Path $log) {
        $size = (Get-Item $log).Length / 1MB
        Write-Host "  📄 Encontrado: $log ($([math]::Round($size, 2)) MB)" -ForegroundColor Yellow
        
        # Crear backup si el archivo es grande
        if ($size -gt 1) {
            $backup = "$log.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Copy-Item $log $backup
            Write-Host "    💾 Backup creado: $backup" -ForegroundColor Green
        }
        
        # Limpiar el archivo
        Clear-Content $log
        Write-Host "    ✅ Limpiado" -ForegroundColor Green
    }
}

# Logs en src/Infrastructure/DjangoFramework
$djangoLogPath = "src\Infrastructure\DjangoFramework\errores_django.log"
if (Test-Path $djangoLogPath) {
    $size = (Get-Item $djangoLogPath).Length / 1MB
    Write-Host "  📄 Encontrado: $djangoLogPath ($([math]::Round($size, 2)) MB)" -ForegroundColor Yellow
    
    if ($size -gt 1) {
        $backup = "$djangoLogPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $djangoLogPath $backup
        Write-Host "    💾 Backup creado: $backup" -ForegroundColor Green
    }
    
    Clear-Content $djangoLogPath
    Write-Host "    ✅ Limpiado" -ForegroundColor Green
}

Write-Host "`n✨ Limpieza completada!" -ForegroundColor Green
Write-Host "💡 Los logs ahora se rotarán automáticamente al alcanzar 5 MB" -ForegroundColor Cyan
