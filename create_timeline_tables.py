"""
Script para crear las tablas de Timeline Period manualmente via SQL.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.db import connection

print("🔧 Creando tablas de Timeline Period manualmente\n")
print("=" * 60)

sql_commands = [
    # Tabla TimelinePeriod
    """
    CREATE TABLE IF NOT EXISTS persistence_timelineperiod (
        id SERIAL PRIMARY KEY,
        world_id VARCHAR(20) NOT NULL REFERENCES caos_worlds(id) ON DELETE CASCADE,
        title VARCHAR(100) NOT NULL,
        slug VARCHAR(100) NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        "order" INTEGER NOT NULL DEFAULT 0,
        is_current BOOLEAN NOT NULL DEFAULT FALSE,
        cover_image VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        UNIQUE(world_id, slug)
    );
    """,
    
    # Índices para TimelinePeriod
    """
    CREATE INDEX IF NOT EXISTS idx_timelineperiod_world_current 
    ON persistence_timelineperiod(world_id, is_current);
    """,
    
    """
    CREATE INDEX IF NOT EXISTS idx_timelineperiod_world_slug 
    ON persistence_timelineperiod(world_id, slug);
    """,
    
    # Tabla TimelinePeriodVersion
    """
    CREATE TABLE IF NOT EXISTS persistence_timelineperiodversion (
        id SERIAL PRIMARY KEY,
        period_id INTEGER NOT NULL REFERENCES persistence_timelineperiod(id) ON DELETE CASCADE,
        version_number INTEGER NOT NULL,
        proposed_title VARCHAR(100) NOT NULL DEFAULT '',
        proposed_description TEXT NOT NULL DEFAULT '',
        status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
        author_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
        reviewer_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
        change_log TEXT NOT NULL DEFAULT '',
        admin_feedback TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        reviewed_at TIMESTAMP WITH TIME ZONE,
        UNIQUE(period_id, version_number)
    );
    """,
]

try:
    with connection.cursor() as cursor:
        for i, sql in enumerate(sql_commands, 1):
            print(f"[{i}/{len(sql_commands)}] Ejecutando comando SQL...")
            cursor.execute(sql)
            print(f"[{i}/{len(sql_commands)}] ✅ Completado")
    
    print("\n" + "=" * 60)
    print("✅ Tablas creadas exitosamente!")
    print("\n💡 Ahora puedes ejecutar create_actual_periods.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
