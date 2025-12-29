# Generated manually for JSONB optimization
from django.db import migrations
from django.contrib.postgres.operations import AddIndexConcurrently


class Migration(migrations.Migration):
    """
    Añade índices GIN (Generalized Inverted Index) para optimizar búsquedas en campos JSONB.
    
    Los índices GIN son ideales para JSONB porque:
    - Permiten búsquedas eficientes en claves específicas
    - Soportan operadores @>, ?, ?&, ?|
    - Mejoran el rendimiento en consultas complejas
    
    Índices creados:
    1. idx_metadata_gin - Índice general en metadata
    2. idx_metadata_timeline - Índice específico para timeline
    3. idx_metadata_gallery_log - Índice para gallery_log
    4. idx_metadata_current_year - Índice para current_year (B-tree)
    """
    
    dependencies = [
        ('persistence', '0028_chronicleeventorm_narrative_summary'),
    ]
    
    # Usar atomic = False para permitir CREATE INDEX CONCURRENTLY
    atomic = False
    
    operations = [
        # 1. Índice GIN general en metadata (para búsquedas generales)
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metadata_gin 
                ON caos_worlds USING GIN (metadata);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_metadata_gin;",
        ),
        
        # 2. Índice GIN específico para timeline (preparado para futuro)
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metadata_timeline 
                ON caos_worlds USING GIN ((metadata->'timeline'));
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_metadata_timeline;",
        ),
        
        # 3. Índice GIN para gallery_log (búsquedas en imágenes)
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metadata_gallery_log 
                ON caos_worlds USING GIN ((metadata->'gallery_log'));
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_metadata_gallery_log;",
        ),
        
        # 4. Índice B-tree para current_year (para filtros y ordenamiento)
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metadata_current_year 
                ON caos_worlds ((metadata->>'current_year'));
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_metadata_current_year;",
        ),
        
        # 5. Índice GIN para datos_nucleo (propiedades físicas)
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metadata_datos_nucleo 
                ON caos_worlds USING GIN ((metadata->'datos_nucleo'));
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_metadata_datos_nucleo;",
        ),
        
        # 6. Índice para tipo_entidad (clasificación)
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metadata_tipo_entidad 
                ON caos_worlds ((metadata->>'tipo_entidad'));
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_metadata_tipo_entidad;",
        ),
    ]
