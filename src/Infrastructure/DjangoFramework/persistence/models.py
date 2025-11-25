from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class CaosWorldORM(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NUEVO: Saber qué versión está viva ahora mismo
    current_version_number = models.IntegerField(default=1)

    class Meta:
        db_table = 'caos_worlds'

class CaosVersionORM(models.Model):
    world = models.ForeignKey(CaosWorldORM, on_delete=models.CASCADE, related_name='versiones')
    proposed_name = models.CharField(max_length=255)
    proposed_description = models.TextField(null=True, blank=True)
    version_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="PENDING")
    change_log = models.CharField(max_length=255, blank=True)
    
    # NUEVO: El autor (Puede ser null si el usuario fue borrado)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'caos_versions'
        ordering = ['-version_number']