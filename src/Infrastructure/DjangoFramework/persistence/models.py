from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import nanoid

# 1. FUNCIÓN GENERADORA
def generate_nanoid():
    return nanoid.generate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-', 10)

# Parche para migraciones antiguas
get_nanoid = generate_nanoid

class CaosEpochORM(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_year = models.IntegerField(default=0)
    end_year = models.IntegerField(null=True, blank=True)
    def __str__(self): return f"[{self.id}] {self.name}"
    class Meta: db_table = 'caos_epochs'; ordering = ['start_year']

class CaosWorldORM(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    
    # NANOID (PUBLIC ID)
    public_id = models.CharField(
        max_length=12, 
        default=generate_nanoid, 
        unique=True, 
        editable=False
    )
    
    id_codificado = models.CharField(max_length=30, blank=True, null=True)
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    id_lore = models.CharField(max_length=40, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, default="DRAFT")
    visible_publico = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    current_version_number = models.IntegerField(default=1)
    current_author_name = models.CharField(max_length=150, default="Sistema", blank=True)
    born_in_epoch = models.ForeignKey(CaosEpochORM, on_delete=models.SET_NULL, null=True, blank=True, related_name='entities_born')
    died_in_epoch = models.ForeignKey(CaosEpochORM, on_delete=models.SET_NULL, null=True, blank=True, related_name='entities_died')
    class Meta: db_table = 'caos_worlds'

class CaosVersionORM(models.Model):
    world = models.ForeignKey(CaosWorldORM, on_delete=models.CASCADE, related_name='versiones')
    proposed_name = models.CharField(max_length=150)
    proposed_description = models.TextField(null=True, blank=True)
    version_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default="PENDING")
    change_log = models.CharField(max_length=255, blank=True)
    cambios = models.JSONField(default=dict, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    es_version_activa = models.BooleanField(default=False)
    class Meta: db_table = 'caos_versions'; ordering = ['-version_number']

class CaosNarrativeORM(models.Model):
    nid = models.CharField(primary_key=True, max_length=50)
    
    # NANOID (PUBLIC ID)
    public_id = models.CharField(
        max_length=12, 
        default=generate_nanoid, 
        unique=True, 
        editable=False
    )
    
    world = models.ForeignKey(CaosWorldORM, on_delete=models.CASCADE, related_name='narrativas')
    menciones = models.ManyToManyField(CaosWorldORM, related_name='menciones_en_narrativa', blank=True)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    narrador = models.CharField(max_length=150, default="???")
    TIPO_CHOICES = [('LORE', '📜 Lore'), ('HISTORIA', '📖 Historia'), ('CAPITULO', '📑 Capítulo'), ('EVENTO', '⚔️ Evento'), ('LEYENDA', '🕯️ Leyenda'), ('REGLA', '⚖️ Regla'), ('BESTIARIO', '🐉 Bestiario')]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='LORE')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = 'caos_narratives'; ordering = ['nid']
