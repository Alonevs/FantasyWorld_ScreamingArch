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
    
    # OWNER / AUTHOR
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_entities')
    
    # PERMISSIONS
    allow_proposals = models.BooleanField(default=True, help_text="Si True, permite propuestas de terceros.")
    
    # CONTROL DE BORRADO LÓGICO (SOFT DELETE)
    is_active = models.BooleanField(default=True, help_text="Si es False, está en la papelera.")
    deleted_at = models.DateTimeField(null=True, blank=True)

    def soft_delete(self):
        """Mueve a la papelera sin destruir datos."""
        self.is_active = False
        self.deleted_at = datetime.now()
        self.save()

    def restore(self):
        """Recupera de la papelera."""
        self.is_active = True
        self.deleted_at = None
        self.save()

    @property
    def is_locked(self):
        return self.status == 'LOCKED'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('ver_mundo', args=[str(self.public_id)]) # Use public_id (NanoID)


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
    current_version_number = models.IntegerField(default=1)
    
    # CONTROL DE BORRADO LÓGICO (SOFT DELETE)
    is_active = models.BooleanField(default=True, help_text="Si es False, está en la papelera.")
    deleted_at = models.DateTimeField(null=True, blank=True)

    def soft_delete(self):
        """Mueve a la papelera sin destruir datos."""
        self.is_active = False
        self.deleted_at = datetime.now()
        self.save()

    def restore(self):
        """Recupera de la papelera."""
        self.is_active = True
        self.deleted_at = None
        self.save()

    class Meta: db_table = 'caos_narratives'; ordering = ['nid']

class CaosNarrativeVersionORM(models.Model):
    narrative = models.ForeignKey(CaosNarrativeORM, on_delete=models.CASCADE, related_name='versiones')
    proposed_title = models.CharField(max_length=200)
    proposed_content = models.TextField()
    version_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default="PENDING") # PENDING, APPROVED, REJECTED, LIVE, ARCHIVED
    action = models.CharField(max_length=20, default="EDIT", choices=[('ADD', 'Crear'), ('EDIT', 'Editar'), ('DELETE', 'Borrar')])
    change_log = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta: db_table = 'caos_narrative_versions'; ordering = ['-version_number']

class CaosEventLog(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100) # e.g., "UPLOAD_PHOTO", "EDIT_WORLD"
    target_id = models.CharField(max_length=100, null=True, blank=True) # JID or NID
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta: db_table = 'caos_event_logs'; ordering = ['-timestamp']

class ContributionProposal(models.Model):
    id = models.AutoField(primary_key=True)
    target_entity = models.ForeignKey(CaosWorldORM, on_delete=models.CASCADE, related_name='proposals')
    proposer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contributions')
    proposed_payload = models.JSONField() # The full metadata or specific changes
    status = models.CharField(max_length=20, default='PENDING') # PENDING, APPROVED_WAITING, REJECTED, PUBLISHED
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_proposals')
    created_at = models.DateTimeField(auto_now_add=True)
    contribution_type = models.CharField(max_length=20, default='EDIT') # EDIT, CREATE, TRANSLATE
    
    class Meta:
        db_table = 'contribution_proposals'
        ordering = ['-created_at']

class CaosImageProposalORM(models.Model):
    id = models.AutoField(primary_key=True)
    world = models.ForeignKey(CaosWorldORM, on_delete=models.CASCADE, related_name='image_proposals')
    image = models.ImageField(upload_to='temp_proposals/', null=True, blank=True) # Nullable for DELETE actions
    title = models.CharField(max_length=150, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=30, default="PENDING") # PENDING, APPROVED, REJECTED
    action = models.CharField(max_length=20, default="ADD", choices=[('ADD', 'Añadir'), ('DELETE', 'Borrar')])
    target_filename = models.CharField(max_length=255, null=True, blank=True) # For DELETE actions
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: db_table = 'caos_image_proposals'; ordering = ['-created_at']

class MetadataTemplate(models.Model):
    entity_type = models.CharField(max_length=50, unique=True)
    schema_definition = models.JSONField(default=dict)
    ui_config = models.JSONField(default=dict)

    def __str__(self):
        return self.entity_type

    class Meta:
        db_table = 'metadata_templates'

class UserProfile(models.Model):
    RANK_CHOICES = [
        ('ADMIN', 'Admin'),
        ('SUBADMIN', 'Subadmin'),
        ('USER', 'User')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='USER')
    # M2M Relationship: A user can have multiple collaborators (minions/partners)
    collaborators = models.ManyToManyField('self', symmetrical=False, related_name='bosses', blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.rank})"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
