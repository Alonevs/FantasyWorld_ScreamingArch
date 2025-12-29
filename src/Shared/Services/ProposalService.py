"""
Servicios para gestionar propuestas de cambios LIVE y TIMELINE.

Este módulo separa claramente los dos flujos de propuestas:
- ProposalService: Para cambios en la versión LIVE (actual)
- TimelineProposalService: Para snapshots temporales (históricos)
"""

from typing import Dict, Any, Optional, List
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM
from src.Shared.Services.MetadataValidator import validate_metadata, validate_timeline_snapshot
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# SERVICIO PARA PROPUESTAS LIVE (Versión Actual)
# ============================================================================

class LiveProposalService:
    """
    Gestiona propuestas de cambios a la versión LIVE (actual) de una entidad.
    
    Este es el flujo tradicional de ECLAI para cambios en la versión publicada.
    """
    
    @staticmethod
    def create_proposal(
        world: CaosWorldORM,
        proposed_name: str,
        proposed_description: str,
        author: User,
        change_log: str = "",
        cambios: Dict[str, Any] = None
    ) -> CaosVersionORM:
        """
        Crea una propuesta de cambio para la versión LIVE.
        
        Args:
            world: Entidad a modificar
            proposed_name: Nuevo nombre propuesto
            proposed_description: Nueva descripción propuesta
            author: Usuario que propone el cambio
            change_log: Razón del cambio
            cambios: Diccionario con cambios adicionales (metadata, etc.)
            
        Returns:
            CaosVersionORM creado
        """
        # Obtener siguiente número de versión
        next_version = LiveProposalService._get_next_version_number(world)
        
        # Crear propuesta
        proposal = CaosVersionORM.objects.create(
            world=world,
            change_type='LIVE',
            proposed_name=proposed_name,
            proposed_description=proposed_description,
            version_number=next_version,
            status='PENDING',
            change_log=change_log,
            cambios=cambios or {},
            author=author
        )
        
        logger.info(f"✅ Propuesta LIVE creada: {proposal.id} para {world.name}")
        return proposal
    
    @staticmethod
    def approve_and_publish(proposal: CaosVersionORM, reviewer: User) -> bool:
        """
        Aprueba y publica una propuesta LIVE.
        
        Args:
            proposal: Propuesta a aprobar
            reviewer: Usuario que aprueba
            
        Returns:
            True si se publicó exitosamente
        """
        if not proposal.is_live_proposal():
            raise ValueError("Esta propuesta no es de tipo LIVE")
        
        if proposal.status != 'PENDING':
            raise ValueError(f"La propuesta debe estar PENDING, está {proposal.status}")
        
        # Actualizar entidad con los cambios propuestos
        world = proposal.world
        world.name = proposal.proposed_name
        world.description = proposal.proposed_description
        world.current_version_number = proposal.version_number
        world.current_author_name = proposal.author.username if proposal.author else "Sistema"
        
        # Aplicar cambios de metadata si existen
        if 'metadata' in proposal.cambios:
            if not world.metadata:
                world.metadata = {}
            world.metadata.update(proposal.cambios['metadata'])
        
        # Aplicar cover_image si existe
        if 'cover_image' in proposal.cambios:
            if not world.metadata:
                world.metadata = {}
            world.metadata['cover_image'] = proposal.cambios['cover_image']
        
        world.save()
        
        # Actualizar propuesta
        proposal.status = 'LIVE'
        proposal.reviewer = reviewer
        proposal.save()
        
        logger.info(f"✅ Propuesta LIVE publicada: {proposal.id}")
        return True
    
    @staticmethod
    def reject(proposal: CaosVersionORM, reviewer: User, feedback: str) -> bool:
        """
        Rechaza una propuesta LIVE.
        """
        if not proposal.is_live_proposal():
            raise ValueError("Esta propuesta no es de tipo LIVE")
        
        proposal.status = 'REJECTED'
        proposal.reviewer = reviewer
        proposal.admin_feedback = feedback
        proposal.save()
        
        logger.info(f"❌ Propuesta LIVE rechazada: {proposal.id}")
        return True
    
    @staticmethod
    def _get_next_version_number(world: CaosWorldORM) -> int:
        """Obtiene el siguiente número de versión disponible."""
        last_version = CaosVersionORM.objects.filter(
            world=world,
            change_type='LIVE'
        ).order_by('-version_number').first()
        
        return (last_version.version_number + 1) if last_version else 1


# ============================================================================
# SERVICIO PARA PROPUESTAS TIMELINE (Snapshots Temporales)
# ============================================================================

class TimelineProposalService:
    """
    Gestiona propuestas de snapshots temporales (históricos).
    
    Este servicio maneja el flujo de Timeline, completamente separado de LIVE.
    """
    
    @staticmethod
    def create_proposal(
        world: CaosWorldORM,
        year: int,
        snapshot: Dict[str, Any],
        author: User,
        change_log: str = ""
    ) -> CaosVersionORM:
        """
        Crea una propuesta de snapshot temporal.
        
        Args:
            world: Entidad para la cual crear el snapshot
            year: Año del snapshot
            snapshot: Diccionario con {description, metadata, images, cover_image}
            author: Usuario que propone el snapshot
            change_log: Razón del snapshot
            
        Returns:
            CaosVersionORM creado
            
        Raises:
            ValueError: Si ya existe una propuesta PENDING para ese año
        """
        # Validar que no exista propuesta pendiente para ese año
        existing = CaosVersionORM.objects.filter(
            world=world,
            change_type='TIMELINE',
            timeline_year=year,
            status='PENDING'
        ).exists()
        
        if existing:
            raise ValueError(f"Ya existe una propuesta pendiente para el año {year}")
        
        # Validar estructura del snapshot
        is_valid, error = validate_timeline_snapshot(snapshot)
        if not is_valid:
            raise ValueError(f"Snapshot inválido: {error}")
        
        # Validar metadata del snapshot
        if 'metadata' in snapshot:
            is_valid, error = validate_metadata(snapshot['metadata'])
            if not is_valid:
                logger.warning(f"Metadata del snapshot tiene advertencias: {error}")
        
        # Obtener siguiente número de versión (compartido con LIVE)
        next_version = TimelineProposalService._get_next_version_number(world)
        
        # Crear propuesta
        proposal = CaosVersionORM.objects.create(
            world=world,
            change_type='TIMELINE',
            timeline_year=year,
            proposed_snapshot=snapshot,
            version_number=next_version,
            status='PENDING',
            change_log=change_log,
            author=author,
            # Campos LIVE vacíos (no se usan para TIMELINE)
            proposed_name=world.name,  # Mantener nombre actual
            proposed_description=""
        )
        
        logger.info(f"✅ Propuesta TIMELINE creada: {proposal.id} para {world.name} año {year}")
        return proposal
    
    @staticmethod
    def approve_and_publish(proposal: CaosVersionORM, reviewer: User) -> bool:
        """
        Aprueba y publica un snapshot temporal.
        
        Args:
            proposal: Propuesta de snapshot a aprobar
            reviewer: Usuario que aprueba
            
        Returns:
            True si se publicó exitosamente
        """
        if not proposal.is_timeline_proposal():
            raise ValueError("Esta propuesta no es de tipo TIMELINE")
        
        if proposal.status != 'PENDING':
            raise ValueError(f"La propuesta debe estar PENDING, está {proposal.status}")
        
        # Actualizar metadata del mundo con el snapshot
        world = proposal.world
        if not world.metadata:
            world.metadata = {}
        
        if 'timeline' not in world.metadata:
            world.metadata['timeline'] = {}
        
        # Publicar snapshot en el año correspondiente
        year_str = str(proposal.timeline_year)
        world.metadata['timeline'][year_str] = proposal.proposed_snapshot
        
        # Actualizar rango de años
        years = [int(y) for y in world.metadata['timeline'].keys()]
        world.metadata['year_range'] = [min(years), max(years)]
        
        # Si no hay current_year, usar el primer año
        if 'current_year' not in world.metadata:
            world.metadata['current_year'] = min(years)
        
        world.save()
        
        # Actualizar propuesta
        proposal.status = 'PUBLISHED'
        proposal.reviewer = reviewer
        proposal.save()
        
        logger.info(f"✅ Snapshot TIMELINE publicado: {proposal.id} año {proposal.timeline_year}")
        return True
    
    @staticmethod
    def reject(proposal: CaosVersionORM, reviewer: User, feedback: str) -> bool:
        """
        Rechaza una propuesta de snapshot temporal.
        """
        if not proposal.is_timeline_proposal():
            raise ValueError("Esta propuesta no es de tipo TIMELINE")
        
        proposal.status = 'REJECTED'
        proposal.reviewer = reviewer
        proposal.admin_feedback = feedback
        proposal.save()
        
        logger.info(f"❌ Propuesta TIMELINE rechazada: {proposal.id}")
        return True
    
    @staticmethod
    def get_timeline_proposals(world: CaosWorldORM, status: str = None) -> List[CaosVersionORM]:
        """
        Obtiene todas las propuestas de timeline para una entidad.
        
        Args:
            world: Entidad
            status: Filtrar por status (opcional)
            
        Returns:
            Lista de propuestas TIMELINE
        """
        queryset = CaosVersionORM.objects.filter(
            world=world,
            change_type='TIMELINE'
        ).order_by('timeline_year')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset)
    
    @staticmethod
    def _get_next_version_number(world: CaosWorldORM) -> int:
        """Obtiene el siguiente número de versión disponible (compartido con LIVE)."""
        last_version = CaosVersionORM.objects.filter(
            world=world
        ).order_by('-version_number').first()
        
        return (last_version.version_number + 1) if last_version else 1


# ============================================================================
# SERVICIO UNIFICADO (Facade)
# ============================================================================

class ProposalService:
    """
    Servicio unificado que delega a LiveProposalService o TimelineProposalService
    según el tipo de propuesta.
    """
    
    @staticmethod
    def create_live_proposal(*args, **kwargs) -> CaosVersionORM:
        """Crea propuesta LIVE. Ver LiveProposalService.create_proposal()"""
        return LiveProposalService.create_proposal(*args, **kwargs)
    
    @staticmethod
    def create_timeline_proposal(*args, **kwargs) -> CaosVersionORM:
        """Crea propuesta TIMELINE. Ver TimelineProposalService.create_proposal()"""
        return TimelineProposalService.create_proposal(*args, **kwargs)
    
    @staticmethod
    def approve_and_publish(proposal: CaosVersionORM, reviewer: User) -> bool:
        """Aprueba y publica una propuesta (detecta automáticamente el tipo)."""
        if proposal.is_timeline_proposal():
            return TimelineProposalService.approve_and_publish(proposal, reviewer)
        else:
            return LiveProposalService.approve_and_publish(proposal, reviewer)
    
    @staticmethod
    def reject(proposal: CaosVersionORM, reviewer: User, feedback: str) -> bool:
        """Rechaza una propuesta (detecta automáticamente el tipo)."""
        if proposal.is_timeline_proposal():
            return TimelineProposalService.reject(proposal, reviewer, feedback)
        else:
            return LiveProposalService.reject(proposal, reviewer, feedback)
    
    @staticmethod
    def get_pending_proposals(change_type: str = None) -> List[CaosVersionORM]:
        """
        Obtiene todas las propuestas pendientes.
        
        Args:
            change_type: Filtrar por tipo ('LIVE', 'TIMELINE', None para todas)
            
        Returns:
            Lista de propuestas PENDING
        """
        queryset = CaosVersionORM.objects.filter(status='PENDING')
        
        if change_type:
            queryset = queryset.filter(change_type=change_type)
        
        return list(queryset.order_by('-created_at'))
