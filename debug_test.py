
import os
import django
from django.conf import settings
from django.test import Client, TestCase
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, User

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

class DebugRetouch(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', password='testpass123')
        self.contributor = User.objects.create_user(username='contributor', password='testpass123')
        self.world = CaosWorldORM.objects.create(
            id='01010101', name='Test World', description='Test Description', author=self.author, status='LIVE'
        )
        self.rejected = CaosVersionORM.objects.create(
            world=self.world, proposed_name='Rejected Name', proposed_description='Rejected Description',
            status='REJECTED', version_number=1, author=self.contributor
        )
        self.client = Client()

    def test_run(self):
        self.client.login(username='contributor', password='testpass123')
        print("Requesting...")
        response = self.client.get(f'/editar/{self.world.id}/', {'src_version': self.rejected.id})
        print(f"Status Code: {response.status_code}")
        content = response.content.decode('utf-8')
        
        if 'Rejected Name' in content:
            print("SUCCESS: 'Rejected Name' found in content.")
        else:
            print("FAILURE: 'Rejected Name' NOT found.")
            # Print context variables
            print("Context 'name':", response.context.get('name'))
            print("Context 'description':", response.context.get('description'))
            
            # Print nearby HTML where name should be
            if 'name="name"' in content:
                idx = content.find('name="name"')
                print("HTML around name input:", content[idx-50:idx+100])

runner = DebugRetouch()
runner._pre_setup()
runner.setUp()
runner.test_run()
runner._post_teardown()
