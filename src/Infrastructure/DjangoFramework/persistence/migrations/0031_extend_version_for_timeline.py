# Generated manually for Timeline proposal system
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Extiende CaosVersionORM para soportar propuestas de Timeline.
    
    Añade campos para distinguir entre:
    - Propuestas LIVE: Cambios a la versión actual de la entidad
    - Propuestas TIMELINE: Snapshots históricos/temporales
    
    Esto permite tener dos flujos de aprobación separados en la misma tabla.
    """
    
    dependencies = [
        ('persistence', '0030_add_metadata_gin_indexes'),
    ]
    
    operations = [
        # 1. Añadir campo change_type
        migrations.AddField(
            model_name='caosversionorm',
            name='change_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('LIVE', 'Cambio en versión actual'),
                    ('TIMELINE', 'Snapshot temporal'),
                    ('METADATA', 'Solo metadata')
                ],
                default='LIVE',
                help_text='Tipo de cambio propuesto'
            ),
        ),
        
        # 2. Añadir campo timeline_year (solo para TIMELINE)
        migrations.AddField(
            model_name='caosversionorm',
            name='timeline_year',
            field=models.IntegerField(
                null=True,
                blank=True,
                help_text='Año del snapshot temporal (solo para change_type=TIMELINE)'
            ),
        ),
        
        # 3. Añadir campo proposed_snapshot (JSONB para snapshots completos)
        migrations.AddField(
            model_name='caosversionorm',
            name='proposed_snapshot',
            field=models.JSONField(
                null=True,
                blank=True,
                help_text='Snapshot temporal completo: {description, metadata, images, cover_image}'
            ),
        ),
        
        # 4. Añadir índice para búsquedas por change_type
        migrations.AddIndex(
            model_name='caosversionorm',
            index=models.Index(fields=['change_type', 'status'], name='idx_change_type_status'),
        ),
        
        # 5. Añadir índice para timeline_year
        migrations.AddIndex(
            model_name='caosversionorm',
            index=models.Index(fields=['timeline_year'], name='idx_timeline_year'),
        ),
        
        # 6. Añadir constraint: timeline_year requerido si change_type=TIMELINE
        migrations.AddConstraint(
            model_name='caosversionorm',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(change_type='TIMELINE', timeline_year__isnull=False) |
                    models.Q(change_type__in=['LIVE', 'METADATA'], timeline_year__isnull=True)
                ),
                name='timeline_year_required_for_timeline'
            ),
        ),
        
        # 7. Añadir constraint: proposed_snapshot requerido si change_type=TIMELINE
        migrations.AddConstraint(
            model_name='caosversionorm',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(change_type='TIMELINE', proposed_snapshot__isnull=False) |
                    models.Q(change_type__in=['LIVE', 'METADATA'])
                ),
                name='proposed_snapshot_required_for_timeline'
            ),
        ),
    ]
