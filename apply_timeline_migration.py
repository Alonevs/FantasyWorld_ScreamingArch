"""
Script para aplicar manualmente la migración de Timeline.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.db import connection

sql_statements = [
    'ALTER TABLE "caos_versions" ADD COLUMN IF NOT EXISTS "change_type" varchar(20) DEFAULT \'LIVE\' NOT NULL;',
    'ALTER TABLE "caos_versions" ADD COLUMN IF NOT EXISTS "timeline_year" integer NULL;',
    'ALTER TABLE "caos_versions" ADD COLUMN IF NOT EXISTS "proposed_snapshot" jsonb NULL;',
    'CREATE INDEX IF NOT EXISTS "idx_change_type_status" ON "caos_versions" ("change_type", "status");',
    'CREATE INDEX IF NOT EXISTS "idx_timeline_year" ON "caos_versions" ("timeline_year");',
    '''ALTER TABLE "caos_versions" ADD CONSTRAINT IF NOT EXISTS "timeline_year_required_for_timeline" 
       CHECK (("change_type" = 'TIMELINE' AND "timeline_year" IS NOT NULL) OR 
              ("change_type" IN ('LIVE', 'METADATA') AND "timeline_year" IS NULL));''',
    '''ALTER TABLE "caos_versions" ADD CONSTRAINT IF NOT EXISTS "proposed_snapshot_required_for_timeline" 
       CHECK (("change_type" = 'TIMELINE' AND "proposed_snapshot" IS NOT NULL) OR 
              ("change_type" IN ('LIVE', 'METADATA')));''',
]

print("🔧 Aplicando migración de Timeline...")

with connection.cursor() as cursor:
    for i, sql in enumerate(sql_statements, 1):
        try:
            print(f"  {i}. Ejecutando: {sql[:60]}...")
            cursor.execute(sql)
            print(f"     ✅ OK")
        except Exception as e:
            print(f"     ⚠️  {e}")

print("\n✅ Migración completada!")
print("\n🔍 Verificando campos...")

from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM
fields = [f.name for f in CaosVersionORM._meta.get_fields()]
print(f"Campos del modelo: {fields}")

if 'change_type' in fields and 'timeline_year' in fields and 'proposed_snapshot' in fields:
    print("\n✅ ¡Todos los campos de Timeline están presentes!")
else:
    print("\n❌ Faltan campos de Timeline")
