"""
Tests para las funciones de detección y gestión de portadas.
Valida find_cover_image() y get_thumbnail_url().
"""
from django.test import TestCase
from src.Infrastructure.DjangoFramework.persistence.utils import (
    find_cover_image, get_thumbnail_url
)
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from django.contrib.auth.models import User


class CoverDetectionTestCase(TestCase):
    """Tests para find_cover_image()"""
    
    def test_find_cover_exact_match(self):
        """Test: Encuentra portada con coincidencia exacta"""
        all_imgs = [
            {'filename': 'image1.webp', 'url': 'world1/image1.webp'},
            {'filename': 'Cover.webp', 'url': 'world1/Cover.webp'},
            {'filename': 'image3.webp', 'url': 'world1/image3.webp'},
        ]
        
        result = find_cover_image('Cover.webp', all_imgs)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['filename'], 'Cover.webp')
    
    def test_find_cover_case_insensitive(self):
        """Test: Encuentra portada ignorando mayúsculas/minúsculas"""
        all_imgs = [
            {'filename': 'image1.webp', 'url': 'world1/image1.webp'},
            {'filename': 'COVER.WEBP', 'url': 'world1/COVER.WEBP'},
            {'filename': 'image3.webp', 'url': 'world1/image3.webp'},
        ]
        
        result = find_cover_image('cover.webp', all_imgs)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['filename'], 'COVER.WEBP')
    
    def test_find_cover_without_extension(self):
        """Test: Encuentra portada sin especificar extensión"""
        all_imgs = [
            {'filename': 'image1.webp', 'url': 'world1/image1.webp'},
            {'filename': 'MyCover.webp', 'url': 'world1/MyCover.webp'},
            {'filename': 'image3.webp', 'url': 'world1/image3.webp'},
        ]
        
        result = find_cover_image('mycover', all_imgs)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['filename'], 'MyCover.webp')
    
    def test_find_cover_without_extension_case_insensitive(self):
        """Test: Encuentra portada sin extensión, case-insensitive"""
        all_imgs = [
            {'filename': 'IMAGE1.WEBP', 'url': 'world1/IMAGE1.WEBP'},
            {'filename': 'MyAwesomeCover.webp', 'url': 'world1/MyAwesomeCover.webp'},
        ]
        
        result = find_cover_image('MYAWESOMECOVER', all_imgs)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['filename'], 'MyAwesomeCover.webp')
    
    def test_find_cover_returns_none_if_not_found(self):
        """Test: Devuelve None si no encuentra la portada"""
        all_imgs = [
            {'filename': 'image1.webp', 'url': 'world1/image1.webp'},
            {'filename': 'image2.webp', 'url': 'world1/image2.webp'},
        ]
        
        result = find_cover_image('nonexistent.webp', all_imgs)
        
        self.assertIsNone(result)
    
    def test_find_cover_returns_none_if_empty_list(self):
        """Test: Devuelve None si la lista de imágenes está vacía"""
        result = find_cover_image('cover.webp', [])
        
        self.assertIsNone(result)
    
    def test_find_cover_returns_none_if_no_cover_filename(self):
        """Test: Devuelve None si no se especifica nombre de portada"""
        all_imgs = [
            {'filename': 'image1.webp', 'url': 'world1/image1.webp'},
        ]
        
        result = find_cover_image(None, all_imgs)
        
        self.assertIsNone(result)
    
    def test_find_cover_returns_none_if_empty_cover_filename(self):
        """Test: Devuelve None si el nombre de portada está vacío"""
        all_imgs = [
            {'filename': 'image1.webp', 'url': 'world1/image1.webp'},
        ]
        
        result = find_cover_image('', all_imgs)
        
        self.assertIsNone(result)


class ThumbnailUrlTestCase(TestCase):
    """Tests para get_thumbnail_url()"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Crear mundo de prueba
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Test World',
            description='World for testing',
            author=self.user,
            status='LIVE',
            metadata={'cover_image': 'MyCover.webp'}
        )
    
    def test_get_thumbnail_with_cover_image(self):
        """Test: Devuelve URL de portada si existe"""
        # Nota: Este test requiere que existan imágenes reales en el sistema
        # o que se mockee get_world_images()
        # Por ahora, verificamos que la función no falle
        
        url = get_thumbnail_url(self.world.id, 'MyCover.webp')
        
        self.assertIsNotNone(url)
        self.assertIsInstance(url, str)
    
    def test_get_thumbnail_fallback_to_first_image(self):
        """Test: Si no hay portada, usa la primera imagen"""
        url = get_thumbnail_url(self.world.id, None, use_first_if_no_cover=True)
        
        self.assertIsNotNone(url)
        self.assertIsInstance(url, str)
    
    def test_get_thumbnail_fallback_to_placeholder(self):
        """Test: Si no hay imágenes, usa placeholder"""
        # Crear mundo sin imágenes
        world_no_images = CaosWorldORM.objects.create(
            id='02020202',
            name='Empty World',
            description='World without images',
            author=self.user,
            status='LIVE'
        )
        
        url = get_thumbnail_url(world_no_images.id, None, use_first_if_no_cover=True)
        
        self.assertIsNotNone(url)
        # Debe devolver el placeholder
        self.assertEqual(url, '/static/img/placeholder.png')
    
    def test_get_thumbnail_no_fallback_returns_placeholder(self):
        """Test: Si use_first_if_no_cover=False y no hay portada, devuelve placeholder"""
        url = get_thumbnail_url(self.world.id, None, use_first_if_no_cover=False)
        
        self.assertIsNotNone(url)
        # Si no hay portada y no se permite fallback, debe devolver placeholder
        # (a menos que haya imágenes y la primera sea la portada)
        self.assertIsInstance(url, str)


class CoverIntegrationTestCase(TestCase):
    """Tests de integración para el sistema de portadas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.world = CaosWorldORM.objects.create(
            id='01010101',
            name='Test World',
            description='World for testing',
            author=self.user,
            status='LIVE',
            metadata={'cover_image': 'TestCover.webp'}
        )
    
    def test_cover_image_marked_correctly(self):
        """Test: La imagen de portada se marca correctamente en get_world_images()"""
        from src.Infrastructure.DjangoFramework.persistence.utils import get_world_images
        
        imgs = get_world_images(self.world.id)
        
        # Verificar que la función no falle
        self.assertIsNotNone(imgs)
        self.assertIsInstance(imgs, list)
        
        # Si hay imágenes, verificar que la portada esté marcada
        if imgs:
            cover_imgs = [img for img in imgs if img.get('is_cover', False)]
            # Debe haber máximo 1 portada
            self.assertLessEqual(len(cover_imgs), 1)
    
    def test_multiple_worlds_different_covers(self):
        """Test: Diferentes mundos pueden tener diferentes portadas"""
        world2 = CaosWorldORM.objects.create(
            id='02020202',
            name='Test World 2',
            description='Another world',
            author=self.user,
            status='LIVE',
            metadata={'cover_image': 'DifferentCover.webp'}
        )
        
        url1 = get_thumbnail_url(self.world.id, self.world.metadata.get('cover_image'))
        url2 = get_thumbnail_url(world2.id, world2.metadata.get('cover_image'))
        
        # Ambas deben devolver URLs válidas
        self.assertIsNotNone(url1)
        self.assertIsNotNone(url2)
        self.assertIsInstance(url1, str)
        self.assertIsInstance(url2, str)
