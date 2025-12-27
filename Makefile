# FantasyWorld - Development Makefile
# Comandos rápidos para desarrollo

.PHONY: help run migrate shell test backup clean format lint check-env

help:
	@echo "FantasyWorld - Comandos Disponibles:"
	@echo ""
	@echo "  make run          - Iniciar servidor de desarrollo"
	@echo "  make migrate      - Ejecutar migraciones de BD"
	@echo "  make shell        - Abrir Django shell"
	@echo "  make test         - Ejecutar tests"
	@echo "  make backup       - Crear backups de BD y medios"
	@echo "  make clean        - Limpiar archivos temporales"
	@echo "  make format       - Formatear código con Black + isort"
	@echo "  make lint         - Verificar código con flake8"
	@echo "  make check-env    - Verificar variables de entorno"
	@echo ""

run:
	@echo "🚀 Iniciando servidor..."
	python server_run.py

migrate:
	@echo "📊 Ejecutando migraciones..."
	python manage.py migrate

shell:
	@echo "🐚 Abriendo Django shell..."
	python manage.py shell

test:
	@echo "🧪 Ejecutando tests..."
	python -m pytest -v

backup:
	@echo "💾 Creando backups..."
	python backup_database.py
	python backup_media.py

clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "✅ Limpieza completada"

format:
	@echo "✨ Formateando código..."
	black src/ --line-length 100
	isort src/ --profile black
	@echo "✅ Código formateado"

lint:
	@echo "🔍 Verificando código..."
	flake8 src/ --max-line-length=100 --exclude=migrations
	@echo "✅ Verificación completada"

check-env:
	@echo "🔐 Verificando entorno..."
	python check_environment.py
