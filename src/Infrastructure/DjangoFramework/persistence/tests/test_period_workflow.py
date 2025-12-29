"""
Tests para el Motor de Periodos (Timeline Periods)
Valida el ciclo completo: Proponer → Aprobar → Publicar
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, 
    TimelinePeriod, 
    TimelinePeriodVersion
)
from src.Shared.Services.TimelinePeriodService import TimelinePeriodService


class PeriodWorkflowTestCase(TestCase):
    """Tests del ciclo de vida completo de periodos"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear usuarios
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.author = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123'
        )
        
        # Crear mundo de prueba
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Test World',
            description='World for testing',
            author=self.author,
            status='LIVE'
        )
        
        # Crear periodo de prueba
        self.period = TimelinePeriod.objects.create(
            world=self.world,
            title='Año 1500',
            description='Periodo de prueba',
            metadata={'era': 'Medieval'},
            is_current=False
        )
        
        self.client = Client()
    
    def test_create_period_proposal(self):
        """Test: Crear una propuesta de nuevo periodo genera TimelinePeriodVersion con status PENDING"""
        # Crear propuesta de edición
        version = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.author,
            title='Año 1500 - Actualizado',
            description='Descripción actualizada',
            metadata={'era': 'Renacimiento'},
            change_log='Corrección histórica'
        )
        
        # Validaciones
        self.assertIsNotNone(version)
        self.assertEqual(version.status, 'PENDING')
        self.assertEqual(version.action, 'EDIT')
        self.assertEqual(version.proposed_title, 'Año 1500 - Actualizado')
        self.assertEqual(version.proposed_description, 'Descripción actualizada')
        self.assertEqual(version.proposed_metadata['era'], 'Renacimiento')
        self.assertEqual(version.author, self.author)
        self.assertEqual(version.version_number, 1)
    
    def test_approve_period_does_not_modify_live(self):
        """Test: Aprobar un periodo NO modifica el periodo Live (solo cambia a APPROVED)"""
        # Crear propuesta
        version = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.author,
            title='Título Nuevo',
            description='Descripción Nueva',
            metadata={'test': 'value'},
            change_log='Test'
        )
        
        # Guardar estado original
        original_title = self.period.title
        original_description = self.period.description
        
        # Aprobar
        TimelinePeriodService.approve_version(version, self.superuser)
        
        # Recargar periodo desde DB
        self.period.refresh_from_db()
        
        # Validaciones
        self.assertEqual(version.status, 'APPROVED')
        self.assertEqual(version.reviewer, self.superuser)
        self.assertIsNotNone(version.reviewed_at)
        
        # El periodo Live NO debe haber cambiado
        self.assertEqual(self.period.title, original_title)
        self.assertEqual(self.period.description, original_description)
    
    def test_publish_approved_period_updates_live(self):
        """Test: Publicar un periodo APPROVED aplica los cambios al periodo Live"""
        # Crear y aprobar propuesta
        version = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.author,
            title='Título Publicado',
            description='Descripción Publicada',
            metadata={'published': True},
            change_log='Test publicación'
        )
        
        TimelinePeriodService.approve_version(version, self.superuser)
        
        # Publicar
        result = TimelinePeriodService.publish_version(version, self.superuser)
        
        # Recargar periodo
        self.period.refresh_from_db()
        
        # Validaciones
        self.assertIsNotNone(result)
        self.assertEqual(self.period.title, 'Título Publicado')
        self.assertEqual(self.period.description, 'Descripción Publicada')
        self.assertEqual(self.period.metadata['published'], True)
    
    def test_cannot_publish_non_approved_period(self):
        """Test: No se puede publicar un periodo que no está APPROVED"""
        version = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.author,
            title='Test',
            description='Test',
            metadata={},
            change_log='Test'
        )
        
        # Intentar publicar sin aprobar
        with self.assertRaises(ValueError) as context:
            TimelinePeriodService.publish_version(version, self.superuser)
        
        self.assertIn('APROBADAS', str(context.exception))
    
    def test_reject_period(self):
        """Test: Rechazar un periodo cambia su status a REJECTED"""
        version = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.author,
            title='Test',
            description='Test',
            metadata={},
            change_log='Test'
        )
        
        # Rechazar
        TimelinePeriodService.reject_version(version, self.superuser, 'No cumple requisitos')
        
        # Validaciones
        self.assertEqual(version.status, 'REJECTED')
        self.assertEqual(version.reviewer, self.superuser)
        self.assertIsNotNone(version.reviewed_at)
    
    def test_delete_period_workflow(self):
        """Test: Workflow de eliminación de periodo"""
        # Crear propuesta de eliminación
        version = TimelinePeriodService.propose_delete(
            period=self.period,
            author=self.author,
            reason='Periodo obsoleto'
        )
        
        # Validaciones de la propuesta
        self.assertEqual(version.action, 'DELETE')
        self.assertEqual(version.status, 'PENDING')
        
        # Aprobar
        TimelinePeriodService.approve_version(version, self.superuser)
        self.assertEqual(version.status, 'APPROVED')
        
        # Guardar ID para verificar eliminación
        period_id = self.period.id
        
        # Publicar (esto debe eliminar el periodo)
        result = TimelinePeriodService.publish_version(version, self.superuser)
        
        # Validaciones
        self.assertIsNone(result)  # publish_version devuelve None cuando elimina
        
        # Verificar que el periodo fue eliminado
        with self.assertRaises(TimelinePeriod.DoesNotExist):
            TimelinePeriod.objects.get(id=period_id)
    
    def test_cannot_delete_current_period(self):
        """Test: No se puede eliminar el periodo actual (is_current=True)"""
        # Marcar periodo como actual
        self.period.is_current = True
        self.period.save()
        
        # Intentar crear propuesta de eliminación (debe fallar aquí)
        with self.assertRaises(ValueError) as context:
            version = TimelinePeriodService.propose_delete(
                period=self.period,
                author=self.author,
                reason='Test'
            )
        
        self.assertIn('ACTUAL', str(context.exception))
    
    def test_metadata_changes_are_tracked(self):
        """Test: Los cambios en metadata se rastrean correctamente"""
        original_metadata = {'era': 'Medieval', 'year': 1500}
        self.period.metadata = original_metadata
        self.period.save()
        
        # Proponer cambios en metadata
        new_metadata = {'era': 'Renacimiento', 'year': 1500, 'new_field': 'value'}
        version = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.author,
            title=self.period.title,
            description=self.period.description,
            metadata=new_metadata,
            change_log='Actualización de metadata'
        )
        
        # Aprobar y publicar
        TimelinePeriodService.approve_version(version, self.superuser)
        TimelinePeriodService.publish_version(version, self.superuser)
        
        # Recargar y validar
        self.period.refresh_from_db()
        self.assertEqual(self.period.metadata['era'], 'Renacimiento')
        self.assertEqual(self.period.metadata['new_field'], 'value')
    
    def test_version_numbering_increments(self):
        """Test: Los números de versión se incrementan correctamente"""
        # Crear múltiples versiones
        v1 = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.author,
            title='V1',
            description='Version 1',
            metadata={},
            change_log='V1'
        )
        
        v2 = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.author,
            title='V2',
            description='Version 2',
            metadata={},
            change_log='V2'
        )
        
        v3 = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.author,
            title='V3',
            description='Version 3',
            metadata={},
            change_log='V3'
        )
        
        # Validar numeración
        self.assertEqual(v1.version_number, 1)
        self.assertEqual(v2.version_number, 2)
        self.assertEqual(v3.version_number, 3)


class PeriodBulkActionsTestCase(TestCase):
    """Tests de acciones masivas (bulk actions)"""
    
    def setUp(self):
        """Configuración inicial"""
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.author = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Test World',
            description='World for testing',
            author=self.author,
            status='LIVE'
        )
        
        # Crear múltiples periodos con slugs únicos
        self.periods = []
        for i in range(5):
            period = TimelinePeriod.objects.create(
                world=self.world,
                title=f'Periodo {i+1}',
                slug=f'periodo-{i+1}',  # Slug único para cada periodo
                description=f'Descripción {i+1}',
                metadata={'index': i+1},
                is_current=False
            )
            self.periods.append(period)
        
        self.client = Client()
    
    def test_bulk_publish_multiple_periods(self):
        """Test: Publicar múltiples periodos a la vez"""
        # Crear y aprobar versiones para todos los periodos
        versions = []
        for period in self.periods:
            version = TimelinePeriodService.propose_edit(
                period=period,
                author=self.author,
                title=f'{period.title} - Updated',
                description=f'{period.description} - Updated',
                metadata={'updated': True},
                change_log='Bulk update'
            )
            TimelinePeriodService.approve_version(version, self.superuser)
            versions.append(version)
        
        # Publicar todos
        published_count = 0
        for version in versions:
            try:
                TimelinePeriodService.publish_version(version, self.superuser)
                published_count += 1
            except Exception:
                pass
        
        # Validar que todos se publicaron
        self.assertEqual(published_count, 5)
        
        # Verificar que los cambios se aplicaron
        for period in self.periods:
            period.refresh_from_db()
            self.assertTrue(period.title.endswith('- Updated'))
            self.assertEqual(period.metadata['updated'], True)
    
    def test_bulk_publish_with_errors_continues(self):
        """Test: Si un periodo falla, los demás continúan publicándose"""
        # Crear versiones
        versions = []
        for i, period in enumerate(self.periods):
            version = TimelinePeriodService.propose_edit(
                period=period,
                author=self.author,
                title=f'Update {i}',
                description='Test',
                metadata={},
                change_log='Test'
            )
            
            # Solo aprobar algunos (los pares)
            if i % 2 == 0:
                TimelinePeriodService.approve_version(version, self.superuser)
            
            versions.append(version)
        
        # Intentar publicar todos
        published_count = 0
        failed_count = 0
        
        for version in versions:
            try:
                TimelinePeriodService.publish_version(version, self.superuser)
                published_count += 1
            except ValueError:
                failed_count += 1
        
        # Validar
        self.assertEqual(published_count, 3)  # Solo los aprobados (0, 2, 4)
        self.assertEqual(failed_count, 2)     # Los no aprobados (1, 3)


class PeriodPermissionsTestCase(TestCase):
    """Tests del sistema de permisos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.author = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123'
        )
        
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Test World',
            description='World for testing',
            author=self.author,
            status='LIVE'
        )
        
        self.period = TimelinePeriod.objects.create(
            world=self.world,
            title='Test Period',
            description='Test',
            metadata={},
            is_current=False
        )
        
        self.version = TimelinePeriodService.propose_edit(
            period=self.period,
            author=self.other_user,
            title='Updated',
            description='Updated',
            metadata={},
            change_log='Test'
        )
        
        self.client = Client()
    
    def test_author_can_approve_own_period(self):
        """Test: El autor del mundo puede aprobar periodos de su mundo"""
        self.client.login(username='author', password='testpass123')
        
        response = self.client.post(f'/periodo/propuesta/{self.version.id}/aprobar/')
        
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, 'APPROVED')
    
    def test_superuser_can_approve_any_period(self):
        """Test: El superuser puede aprobar cualquier periodo"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(f'/periodo/propuesta/{self.version.id}/aprobar/')
        
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, 'APPROVED')
    
    def test_non_author_cannot_approve(self):
        """Test: Un usuario que no es autor ni superuser no puede aprobar"""
        # Crear otro usuario y otro mundo
        another_user = User.objects.create_user(
            username='another',
            email='another@test.com',
            password='testpass123'
        )
        
        self.client.login(username='another', password='testpass123')
        
        response = self.client.post(f'/periodo/propuesta/{self.version.id}/aprobar/')
        
        # Debe redirigir con error
        self.assertEqual(response.status_code, 302)
        
        # El status no debe haber cambiado
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, 'PENDING')
    
    def test_anonymous_cannot_approve(self):
        """Test: Un usuario anónimo no puede aprobar"""
        # No hacer login
        response = self.client.post(f'/periodo/propuesta/{self.version.id}/aprobar/')
        
        # Debe redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
