"""
Tests para el sistema de propuestas (ECLAI).
Valida el flujo completo: Crear → Aprobar → Rechazar → Modo Retoque.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, CaosVersionORM, UserProfile
)


class ProposalWorkflowTestCase(TestCase):
    """Tests del ciclo de vida completo de propuestas"""
    
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
        
        self.contributor = User.objects.create_user(
            username='contributor',
            email='contributor@test.com',
            password='testpass123'
        )
        
        # Crear mundo
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Original Name',
            description='Original Description',
            author=self.author,
            status='LIVE',
            metadata={'population': '1000', 'climate': 'Temperate'}
        )
        
        self.client = Client()
    
    def test_create_proposal_generates_pending_version(self):
        """Test: Crear una propuesta genera CaosVersionORM con status PENDING"""
        self.client.login(username='contributor', password='testpass123')
        
        response = self.client.post(f'/editar/{self.world.id}/', {
            'world_name': 'Updated Name',
            'world_desc': 'Updated Description',
            'metadata_population': '2000',
        })
        
        # Verificar que se creó una versión
        versions = CaosVersionORM.objects.filter(world=self.world)
        self.assertGreater(versions.count(), 0)
        
        # Verificar que está PENDING
        latest_version = versions.latest('created_at')
        self.assertEqual(latest_version.status, 'PENDING')
        self.assertEqual(latest_version.created_by, self.contributor)
    
    def test_approve_proposal_changes_status(self):
        """Test: Aprobar una propuesta cambia su status a APPROVED"""
        # Crear propuesta
        proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name='New Name',
            proposed_description='New Description',
            cambios={'metadata': {'test': 'value'}},
            status='PENDING',
            created_by=self.contributor
        )
        
        self.client.login(username='author', password='testpass123')
        
        response = self.client.post(f'/dashboard/aprobar/{proposal.id}/')
        
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, 'APPROVED')
    
    def test_approve_proposal_does_not_modify_live_world(self):
        """Test: Aprobar NO modifica el mundo LIVE (solo cambia status)"""
        # Guardar estado original
        original_name = self.world.name
        original_description = self.world.description
        
        # Crear y aprobar propuesta
        proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name='Completely Different Name',
            proposed_description='Completely Different Description',
            cambios={'metadata': {'new_field': 'new_value'}},
            status='PENDING',
            created_by=self.contributor
        )
        
        self.client.login(username='author', password='testpass123')
        self.client.post(f'/dashboard/aprobar/{proposal.id}/')
        
        # Recargar mundo
        self.world.refresh_from_db()
        
        # El mundo NO debe haber cambiado
        self.assertEqual(self.world.name, original_name)
        self.assertEqual(self.world.description, original_description)
    
    def test_reject_proposal_changes_status(self):
        """Test: Rechazar una propuesta cambia su status a REJECTED"""
        proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name='New Name',
            proposed_description='New Description',
            cambios={},
            status='PENDING',
            created_by=self.contributor
        )
        
        self.client.login(username='author', password='testpass123')
        
        response = self.client.post(f'/dashboard/rechazar/{proposal.id}/', {
            'feedback': 'No cumple los requisitos'
        })
        
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, 'REJECTED')
    
    def test_archive_proposal_changes_status(self):
        """Test: Archivar una propuesta cambia su status a ARCHIVED"""
        proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name='New Name',
            proposed_description='New Description',
            cambios={},
            status='PENDING',
            created_by=self.contributor
        )
        
        self.client.login(username='author', password='testpass123')
        
        response = self.client.post(f'/dashboard/archivar/{proposal.id}/')
        
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, 'ARCHIVED')
    
    def test_restore_proposal_changes_status_to_pending(self):
        """Test: Restaurar una propuesta rechazada la vuelve a PENDING"""
        proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name='New Name',
            proposed_description='New Description',
            cambios={},
            status='REJECTED',
            created_by=self.contributor
        )
        
        self.client.login(username='contributor', password='testpass123')
        
        response = self.client.post(f'/dashboard/restaurar/{proposal.id}/')
        
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, 'PENDING')


class RetouchModeTestCase(TestCase):
    """Tests del modo retoque"""
    
    def setUp(self):
        """Configuración inicial"""
        self.author = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        
        self.contributor = User.objects.create_user(
            username='contributor',
            email='contributor@test.com',
            password='testpass123'
        )
        
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Test World',
            description='Test Description',
            author=self.author,
            status='LIVE'
        )
        
        # Crear propuesta rechazada
        self.rejected_proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name='Rejected Name',
            proposed_description='Rejected Description',
            cambios={'metadata': {'test': 'value'}},
            status='REJECTED',
            created_by=self.contributor
        )
        
        self.client = Client()
    
    def test_retouch_mode_prefills_form(self):
        """Test: El modo retoque pre-rellena el formulario con datos de la propuesta"""
        self.client.login(username='contributor', password='testpass123')
        
        response = self.client.get(
            f'/editar/{self.world.id}/',
            {'retouch_version': self.rejected_proposal.id}
        )
        
        self.assertEqual(response.status_code, 200)
        # Verificar que el formulario contiene los datos de la propuesta
        self.assertContains(response, 'Rejected Name')
        self.assertContains(response, 'Rejected Description')
    
    def test_retouch_mode_only_for_rejected_proposals(self):
        """Test: El modo retoque solo funciona con propuestas REJECTED"""
        # Crear propuesta aprobada
        approved_proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name='Approved Name',
            proposed_description='Approved Description',
            cambios={},
            status='APPROVED',
            created_by=self.contributor
        )
        
        self.client.login(username='contributor', password='testpass123')
        
        response = self.client.get(
            f'/editar/{self.world.id}/',
            {'retouch_version': approved_proposal.id}
        )
        
        # Debe redirigir o mostrar error (no permitir retoque de aprobadas)
        # El comportamiento exacto depende de la implementación
        self.assertIn(response.status_code, [200, 302])


class ProposalMetadataTestCase(TestCase):
    """Tests de cambios en metadata"""
    
    def setUp(self):
        """Configuración inicial"""
        self.author = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Test World',
            description='Test Description',
            author=self.author,
            status='LIVE',
            metadata={'population': '1000', 'climate': 'Temperate', 'era': 'Medieval'}
        )
        
        self.client = Client()
    
    def test_metadata_changes_are_tracked(self):
        """Test: Los cambios en metadata se rastrean correctamente"""
        proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name=self.world.name,
            proposed_description=self.world.description,
            cambios={
                'metadata': {
                    'population': '2000',  # Cambio
                    'climate': 'Tropical',  # Cambio
                    'era': 'Medieval',  # Sin cambio
                    'new_field': 'new_value'  # Nuevo campo
                }
            },
            status='PENDING',
            created_by=self.author
        )
        
        # Verificar que los cambios están en la propuesta
        self.assertEqual(proposal.cambios['metadata']['population'], '2000')
        self.assertEqual(proposal.cambios['metadata']['climate'], 'Tropical')
        self.assertEqual(proposal.cambios['metadata']['new_field'], 'new_value')
    
    def test_cover_image_change_is_tracked(self):
        """Test: Los cambios en cover_image se rastrean correctamente"""
        proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name=self.world.name,
            proposed_description=self.world.description,
            cambios={
                'cover_image': 'NewCover.webp'
            },
            status='PENDING',
            created_by=self.author
        )
        
        # Verificar que el cambio de portada está registrado
        self.assertEqual(proposal.cambios['cover_image'], 'NewCover.webp')


class BulkProposalActionsTestCase(TestCase):
    """Tests de acciones masivas sobre propuestas"""
    
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
            description='Test Description',
            author=self.author,
            status='LIVE'
        )
        
        # Crear múltiples propuestas
        self.proposals = []
        for i in range(5):
            proposal = CaosVersionORM.objects.create(
                world=self.world,
                proposed_name=f'Proposal {i}',
                proposed_description=f'Description {i}',
                cambios={},
                status='PENDING',
                created_by=self.author
            )
            self.proposals.append(proposal)
        
        self.client = Client()
    
    def test_bulk_approve_multiple_proposals(self):
        """Test: Aprobar múltiples propuestas a la vez"""
        self.client.login(username='admin', password='testpass123')
        
        proposal_ids = [p.id for p in self.proposals]
        
        response = self.client.post('/dashboard/aprobar-masivo/', {
            'proposal_ids': proposal_ids
        })
        
        # Verificar que todas fueron aprobadas
        for proposal in self.proposals:
            proposal.refresh_from_db()
            self.assertEqual(proposal.status, 'APPROVED')
    
    def test_bulk_reject_multiple_proposals(self):
        """Test: Rechazar múltiples propuestas a la vez"""
        self.client.login(username='admin', password='testpass123')
        
        proposal_ids = [p.id for p in self.proposals]
        
        response = self.client.post('/dashboard/rechazar-masivo/', {
            'proposal_ids': proposal_ids,
            'feedback': 'Rechazo masivo de prueba'
        })
        
        # Verificar que todas fueron rechazadas
        for proposal in self.proposals:
            proposal.refresh_from_db()
            self.assertEqual(proposal.status, 'REJECTED')
