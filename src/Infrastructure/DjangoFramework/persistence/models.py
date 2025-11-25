from django.db import models
from django.contrib.auth.models import User

class CaosWorldORM(models.Model):
    # --- TABLA CAOS (Según tabla caos.docx) ---
    id = models.CharField(primary_key=True, max_length=100)  # id_caos (Siempre 01, 0101...)
    
    # Identificación
    id_codificado = models.CharField(max_length=30, blank=True, null=True) # id_codificado
    name = models.CharField(max_length=150)  # nombre
    
    # Contenido
    description = models.TextField(null=True, blank=True)  # descripcion_conceptual
    id_lore = models.CharField(max_length=40, null=True, blank=True) # id_lore (Enlace a narrativa)
    metadata = models.JSONField(default=dict, blank=True)  # metadata (Datos extra: edad, stats...)
    
    # Control
    status = models.CharField(max_length=50, default="DRAFT") 
    visible_publico = models.BooleanField(default=False)   # visible_publico
    eliminada = models.BooleanField(default=False)         # eliminada (Soft delete)
    created_at = models.DateTimeField(auto_now_add=True)   # fecha_creacion
    
    # Versionado Live
    current_version_number = models.IntegerField(default=1) # version_actual
    current_author_name = models.CharField(max_length=150, default="Sistema", blank=True)

    class Meta:
        db_table = 'caos_worlds'

class CaosVersionORM(models.Model):
    # --- TABLA VERSION (Según tabla caos_version.docx) ---
    world = models.ForeignKey(CaosWorldORM, on_delete=models.CASCADE, related_name='versiones') # id_caos
    
    # Contenido de la revisión
    proposed_name = models.CharField(max_length=150)
    proposed_description = models.TextField(null=True, blank=True)
    
    # Metadatos Versión
    version_number = models.IntegerField() # numero_version
    created_at = models.DateTimeField(auto_now_add=True) # fecha_version
    status = models.CharField(max_length=30, default="PENDING") # estado
    
    # Auditoría
    change_log = models.CharField(max_length=255, blank=True) # descripcion_version (Razón)
    cambios = models.JSONField(default=dict, blank=True) # cambios (JSON con el delta exacto)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) # autor
    
    # Flags
    es_version_activa = models.BooleanField(default=False) # es_version_activa

    class Meta:
        db_table = 'caos_versions'
        ordering = ['-version_number']