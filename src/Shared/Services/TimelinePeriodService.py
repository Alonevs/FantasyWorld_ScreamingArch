"""
Servicio para gestionar períodos temporales (Timeline Periods).
Maneja la creación, edición, aprobación y eliminación de períodos históricos.
"""
from django.utils.text import slugify
from django.utils import timezone
from django.db import models
from src.Infrastructure.DjangoFramework.persistence.models import (
    TimelinePeriod, 
    TimelinePeriodVersion,
    CaosWorldORM,
    CaosNotification
)


class TimelinePeriodService:
    """
    Servicio para gestionar períodos temporales independientes.
    Cada período tiene su propia descripción, fotos, narrativas y versiones.
    """
    
    @staticmethod
    def create_period(world, title, description, author, order=None, is_future=False):
        """
        Crea un nuevo período temporal.
        
        Args:
            world: CaosWorldORM instance
            title: Título del período (ej: "Inicios", "Expansión")
            description: Descripción/lore del período
            author: User que crea el período
            order: Orden de visualización (opcional, auto-calculado si None)
        
        Returns:
            TimelinePeriod instance
        """
        # Generar slug único
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        
        while TimelinePeriod.objects.filter(world=world, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Calcular order si no se proporciona
        if order is None:
            max_order = TimelinePeriod.objects.filter(world=world).aggregate(
                models.Max('order')
            )['order__max']
            order = (max_order or 0) + 1
        
        # Crear período
        period = TimelinePeriod.objects.create(
            world=world,
            title=title,
            slug=slug,
            description=description,
            order=order,
            is_current=False,  # Solo ACTUAL puede ser is_current=True
            is_future=is_future
        )
        
        # Crear versión inicial (V-1) para no interferir con el conteo de propuestas (V0, V1...)
        TimelinePeriodVersion.objects.create(
            period=period,
            version_number=-1,
            proposed_title=title,
            proposed_description=description,
            proposed_metadata=period.metadata,
            action='ADD',
            status='APPROVED',
            author=author,
            change_log='Creación inicial del período'
        )
        
        return period
    
    @staticmethod
    def propose_edit(period, title=None, description=None, metadata=None, author=None, change_log=''):
        """
        Propone cambios a un período existente.
        Crea una nueva versión en estado PENDING.
        
        Args:
            period: TimelinePeriod instance
            title: Nuevo título (opcional, mantiene actual si None)
            description: Nueva descripción (opcional, mantiene actual si None)
            metadata: Nuevos metadatos (opcional)
            author: User que propone el cambio
            change_log: Descripción de los cambios
        
        Returns:
            TimelinePeriodVersion instance
        """
        # Calcular siguiente número de versión (v0 para la primera propuesta real si no hay previas)
        last_version = period.versions.aggregate(models.Max('version_number'))['version_number__max']
        next_version = (last_version + 1) if last_version is not None else 0
        
        # Crear versión propuesta
        version = TimelinePeriodVersion.objects.create(
            period=period,
            version_number=next_version,
            proposed_title=title or period.title,
            proposed_description=description or period.description,
            proposed_metadata=metadata if metadata is not None else period.metadata,
            action='EDIT',
            status='PENDING',
            author=author,
            change_log=change_log or f'Propuesta de cambios v{next_version}'
        )
        
        return version

    @staticmethod
    def propose_delete(period, author, reason=''):
        """
        Propone la eliminación de un período.
        Crea una nueva versión en estado PENDING con action='DELETE'.
        """
        if period.is_current:
            raise ValueError("No se puede proponer eliminar el período ACTUAL")

        last_version = period.versions.aggregate(models.Max('version_number'))['version_number__max']
        next_version = (last_version + 1) if last_version is not None else 0
        
        version = TimelinePeriodVersion.objects.create(
            period=period,
            version_number=next_version,
            proposed_title=period.title,
            proposed_description=period.description,
            proposed_metadata=period.metadata,
            action='DELETE',
            status='PENDING',
            author=author,
            change_log=reason or f'Propuesta de eliminación del período'
        )
        
        return version
    
    @staticmethod
    def approve_version(version, reviewer):
        """
        Aprueba una versión (Estado: APPROVED).
        NO publica los cambios al Live todavía.
        
        Args:
            version: TimelinePeriodVersion instance
            reviewer: User que aprueba (admin)
        """
        version.status = 'APPROVED'
        version.reviewer = reviewer
        version.reviewed_at = timezone.now()
        version.save()

        # Create Notification
        if version.author:
            CaosNotification.objects.create(
                user=version.author,
                title="📅 Periodo Aprobado",
                message=f"Tu propuesta para el periodo '{version.period.title}' de '{version.period.world.name}' ha sido aprobada.",
                url=f"/dashboard/?type=PERIOD"
            )

        return version

    @staticmethod
    def publish_version(version, user=None):
        """
        Publica una versión APROBADA al entorno LIVE.
        Actualiza los datos del TimelinePeriod.
        
        Args:
            version: TimelinePeriodVersion instance
            user: User que publica (opcional)
            
        Returns:
            TimelinePeriod instance actualizado o None (si fue borrado)
        """
        if version.status != 'APPROVED':
            raise ValueError("Solo se pueden publicar versiones APROBADAS.")

        period = version.period

        # --- LÓGICA POR ACCIÓN ---
        if version.action == 'DELETE':
            # Si la acción es eliminar, borramos el periodo
            if period.is_current:
                raise ValueError("No se puede aprobar la eliminación del período ACTUAL")
            period.delete()
            return None

        # Para ADD y EDIT, actualizamos el período con los cambios propuestos
        if version.proposed_title and version.proposed_title != period.title:
            period.title = version.proposed_title
            period.slug = slugify(version.proposed_title)
        
        if version.proposed_description:
            period.description = version.proposed_description
        
        if version.proposed_metadata is not None:
            period.metadata = version.proposed_metadata
        
        # Actualizar número de versión actual
        period.current_version_number = version.version_number
        period.save()
        
        # 1. Archive previous LIVE versions for this period
        # Convert any existing 'LIVE' version to 'HISTORY' to preserve the record
        previous_live = TimelinePeriodVersion.objects.filter(
            period=period, 
            status='LIVE'
        ).exclude(id=version.id)
        
        for old_v in previous_live:
            old_v.status = 'HISTORY'
            old_v.save()

        # 2. Update New Version Status to LIVE
        version.status = 'LIVE'
        version.save()
        
        # Create Notification
        if version.author:
            CaosNotification.objects.create(
                user=version.author,
                title="🚀 ¡Periodo Publicado!",
                message=f"Tu propuesta para el periodo '{period.title}' de '{period.world.name}' ya está en vivo.",
                url=f"/mundo/{period.world.public_id}/?period={period.slug}"
            )

        return period
    
    @staticmethod
    def reject_version(version, reviewer, feedback=''):
        """
        Rechaza una versión propuesta.
        
        Args:
            version: TimelinePeriodVersion instance
            reviewer: User que rechaza (admin)
            feedback: Razón del rechazo
        
        Returns:
            TimelinePeriodVersion instance actualizado
        """
        version.status = 'REJECTED'
        version.reviewer = reviewer
        version.reviewed_at = timezone.now()
        version.admin_feedback = feedback
        version.save()
        
        # Create Notification
        if version.author:
            feedback_msg = f" Motivo: {feedback}" if feedback else ""
            CaosNotification.objects.create(
                user=version.author,
                title="❌ Periodo Rechazado",
                message=f"Tu propuesta para el periodo '{version.period.title}' en '{version.period.world.name}' ha sido rechazada.{feedback_msg}",
                url=f"/dashboard/?type=PERIOD"
            )

        return version
    
    @staticmethod
    def delete_period(period):
        """
        Elimina un período temporal.
        NOTA: No se puede eliminar el período ACTUAL.
        
        Args:
            period: TimelinePeriod instance
        
        Raises:
            ValueError: Si se intenta eliminar el período ACTUAL
        """
        if period.is_current:
            raise ValueError("No se puede eliminar el período ACTUAL")
        
        # Django eliminará automáticamente las versiones relacionadas (CASCADE)
        period.delete()
    
    @staticmethod
    def get_periods_for_world(world):
        """
        Obtiene todos los períodos de una entidad, ordenados.
        
        Args:
            world: CaosWorldORM instance
        
        Returns:
            QuerySet de TimelinePeriod
        """
        return TimelinePeriod.objects.filter(world=world).order_by('order', 'created_at')
    
    @staticmethod
    def get_current_period(world):
        """
        Obtiene el período ACTUAL de una entidad.
        
        Args:
            world: CaosWorldORM instance
        
        Returns:
            TimelinePeriod instance o None
        """
        return TimelinePeriod.objects.filter(world=world, is_current=True).first()

    @staticmethod
    def activate_period(period, user):
        """
        Convierte un período (Futuro o Histórico) en el ACTUAL (Live).
        El antiguo ACTUAL pasa a ser Histórico.
        """
        world = period.world
        current = TimelinePeriodService.get_current_period(world)
        
        if current:
            # El antiguo actual pasa a historia
            current.is_current = False
            current.is_future = False
            current.save()
            
        # El nuevo pasa a actual/live
        period.is_current = True
        period.is_future = False
        period.save()
        
        return period

    @staticmethod
    def resolve_period(world, slug):
        """
        Resuelve un slug de periodo a una instancia de TimelinePeriod.
        Soporta 'actual' para obtener el periodo activo.
        """
        if not slug or slug == 'actual':
            return TimelinePeriodService.get_current_period(world)
        
        try:
            return TimelinePeriod.objects.get(world=world, slug=slug)
        except TimelinePeriod.DoesNotExist:
            return None
