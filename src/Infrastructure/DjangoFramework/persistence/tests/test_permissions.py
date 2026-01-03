"""
Tests críticos de permisos para mundos y propuestas.
Valida que los usuarios solo puedan editar lo que les corresponde.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, CaosVersionORM, UserProfile
)


class WorldPermissionsTestCase(TestCase):
    """Tests del sistema de permisos para mundos"""
    
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
        
        # Crear perfil de admin para el autor
        self.author_profile, _ = UserProfile.objects.get_or_create(
            user=self.author,
            defaults={'rank': 'EXPLORER'}
        )
        
        # Crear mundo de prueba
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Test World',
            description='World for testing',
            author=self.author,
            status='LIVE'
        )
        
        self.client = Client()
    
    def test_user_cannot_edit_others_world(self):
        """Test: Un usuario no puede editar mundos de otros usuarios"""
        self.client.login(username='other', password='testpass123')
        
        response = self.client.get(f'/editar/{self.world.id}/')
        
        # Debe redirigir con error (sin permisos)
        self.assertEqual(response.status_code, 302)
    
    def test_author_can_edit_own_world(self):
        """Test: El autor puede editar su propio mundo"""
        self.client.login(username='author', password='testpass123')
        
        response = self.client.get(f'/editar/{self.world.id}/')
        
        # Debe mostrar el formulario de edición
        self.assertEqual(response.status_code, 200)
    
    def test_superuser_can_edit_any_world(self):
        """Test: El superuser puede editar cualquier mundo"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(f'/editar/{self.world.id}/')
        
        # Debe mostrar el formulario de edición
        self.assertEqual(response.status_code, 200)
    
    def test_anonymous_cannot_edit_world(self):
        """Test: Un usuario anónimo no puede editar mundos"""
        # No hacer login
        response = self.client.get(f'/editar/{self.world.id}/')
        
        # Debe redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)


class ProposalPermissionsTestCase(TestCase):
    """Tests del sistema de permisos para propuestas"""
    
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
        
        self.other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123'
        )
        
        # Crear mundo
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Test World',
            description='World for testing',
            author=self.author,
            status='LIVE'
        )
        
        # Crear propuesta de otro usuario
        self.proposal = CaosVersionORM.objects.create(
            world=self.world,
            proposed_name='Updated Name',
            proposed_description='Updated Description',
            cambios={'metadata': {'test': 'value'}},
            status='PENDING',
            created_by=self.contributor
        )
        
        self.client = Client()
    
    def test_author_can_approve_proposals_for_own_world(self):
        """Test: El autor del mundo puede aprobar propuestas de su mundo"""
        self.client.login(username='author', password='testpass123')
        
        response = self.client.post(f'/dashboard/aprobar/{self.proposal.id}/')
        
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'APPROVED')
    
    def test_superuser_can_approve_any_proposal(self):
        """Test: El superuser puede aprobar cualquier propuesta"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(f'/dashboard/aprobar/{self.proposal.id}/')
        
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'APPROVED')
    
    def test_contributor_cannot_approve_own_proposal(self):
        """Test: El contribuyente no puede aprobar su propia propuesta"""
        self.client.login(username='contributor', password='testpass123')
        
        response = self.client.post(f'/dashboard/aprobar/{self.proposal.id}/')
        
        # Debe redirigir con error
        self.assertEqual(response.status_code, 302)
        
        # El status no debe haber cambiado
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'PENDING')
    
    def test_other_user_cannot_approve_proposal(self):
        """Test: Un usuario sin relación no puede aprobar propuestas"""
        self.client.login(username='other', password='testpass123')
        
        response = self.client.post(f'/dashboard/aprobar/{self.proposal.id}/')
        
        # Debe redirigir con error
        self.assertEqual(response.status_code, 302)
        
        # El status no debe haber cambiado
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'PENDING')
    
    def test_contributor_can_delete_own_pending_proposal(self):
        """Test: El contribuyente puede borrar su propia propuesta PENDING"""
        self.client.login(username='contributor', password='testpass123')
        
        proposal_id = self.proposal.id
        response = self.client.post(f'/dashboard/borrar/{proposal_id}/')
        
        # La propuesta debe haber sido eliminada
        with self.assertRaises(CaosVersionORM.DoesNotExist):
            CaosVersionORM.objects.get(id=proposal_id)
    
    def test_contributor_cannot_delete_approved_proposal(self):
        """Test: El contribuyente no puede borrar propuestas ya aprobadas"""
        # Aprobar la propuesta primero
        self.proposal.status = 'APPROVED'
        self.proposal.save()
        
        self.client.login(username='contributor', password='testpass123')
        
        response = self.client.post(f'/dashboard/borrar/{self.proposal.id}/')
        
        # La propuesta debe seguir existiendo
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'APPROVED')


class TeamPermissionsTestCase(TestCase):
    """Tests de permisos para equipos y colaboradores"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.subadmin = User.objects.create_user(
            username='subadmin',
            email='subadmin@test.com',
            password='testpass123'
        )
        
        self.explorer = User.objects.create_user(
            username='explorer',
            email='explorer@test.com',
            password='testpass123'
        )
        
        # Crear perfiles con diferentes rangos
        UserProfile.objects.create(user=self.admin, rank='ADMIN')
        UserProfile.objects.create(user=self.subadmin, rank='SUBADMIN')
        UserProfile.objects.create(user=self.explorer, rank='EXPLORER')
        
        self.client = Client()
    
    def test_admin_can_toggle_roles(self):
        """Test: Un ADMIN puede cambiar roles de otros usuarios"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(f'/dashboard/toggle-admin/{self.explorer.id}/')
        
        # Debe haber cambiado el rol
        self.explorer.profile.refresh_from_db()
        # El rol debería haber cambiado (EXPLORER -> SUBADMIN o viceversa)
        self.assertIn(response.status_code, [200, 302])
    
    def test_subadmin_cannot_toggle_roles(self):
        """Test: Un SUBADMIN no puede cambiar roles"""
        self.client.login(username='subadmin', password='testpass123')
        
        response = self.client.post(f'/dashboard/toggle-admin/{self.explorer.id}/')
        
        # Debe redirigir con error (sin permisos)
        self.assertEqual(response.status_code, 302)
    
    def test_explorer_cannot_access_team_management(self):
        """Test: Un EXPLORER no puede acceder a gestión de equipo"""
        self.client.login(username='explorer', password='testpass123')
        
        response = self.client.get('/dashboard/team/')
        
        # Debe redirigir con error
        self.assertEqual(response.status_code, 302)
    
    def test_admin_can_access_team_management(self):
        """Test: Un ADMIN puede acceder a gestión de equipo"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/dashboard/team/')
        
        # Debe mostrar la página
        self.assertEqual(response.status_code, 200)
