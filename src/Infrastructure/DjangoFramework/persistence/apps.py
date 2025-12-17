from django.apps import AppConfig

class PersistenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # AQUÍ ESTABA EL PROBLEMA: Antes decía name = 'persistence'
    name = 'src.Infrastructure.DjangoFramework.persistence'

    def ready(self):
        import src.Infrastructure.DjangoFramework.persistence.signals
