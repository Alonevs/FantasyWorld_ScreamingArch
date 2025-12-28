import re
from django.core.management.base import BaseCommand
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosNarrativeORM

class Command(BaseCommand):
    help = 'Verifica enlaces internos (J-IDs y Public IDs) en las narrativas.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🔍 Iniciando verificación de enlaces...'))
        
        narrativas = CaosNarrativeORM.objects.filter(is_active=True)
        broken_count = 0
        total_links = 0
        
        # Patrón para J-IDs (Asumiendo 16 caracteres alfanuméricos o formato 0105...)
        # Y Patrón para URLs internas /mundo/ID/ o /narrativa/ID/
        patterns = [
            r'\/mundo\/([a-zA-Z0-9_\-]+)\/',
            r'\/narrativa\/([a-zA-Z0-9_\-]+)\/',
            r'J-ID:?\s*([a-zA-Z0-9]{10,20})' # Búsqueda de menciones textuales
        ]
        
        for n in narrativas:
            content = n.contenido
            found_in_this = 0
            
            for p in patterns:
                matches = re.findall(p, content)
                for match in matches:
                    total_links += 1
                    exists = False
                    
                    # Verificar si es Mundo
                    if CaosWorldORM.objects.filter(id=match).exists() or \
                       CaosWorldORM.objects.filter(public_id=match).exists():
                        exists = True
                    
                    # Verificar si es Narrativa
                    if not exists:
                        if CaosNarrativeORM.objects.filter(nid=match).exists() or \
                           CaosNarrativeORM.objects.filter(public_id=match).exists():
                            exists = True
                    
                    if not exists:
                        self.stdout.write(self.style.WARNING(
                            f'❌ Enlace roto en "{n.titulo}" ({n.public_id}): "{match}"'
                        ))
                        broken_count += 1
                        found_in_this += 1
            
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Verificación completada.\n'
            f'📊 Total enlaces analizados: {total_links}\n'
            f'⚠️ Enlaces rotos hallados: {broken_count}'
        ))
