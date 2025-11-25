from django.db import models
from datetime import datetime

class CaosWorldORM(models.Model):
    # ID como texto para soportar tus códigos ECLAI (ej. '01')
    id = models.CharField(primary_key=True, max_length=100)
    
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default="DRAFT")
    
    # EL CAMPO QUE FALTABA:
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'caos_worlds'
