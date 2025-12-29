from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import nanoid

# --- FUNCIONES DE UTILIDAD ---

def generate_nanoid():
    """
    Genera un identificador público único de 10 caracteres (NanoID).
    Utiliza un alfabeto personalizado seguro para URLs y referencias externas.
    """
    return nanoid.generate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-', 10)

# Parche para migraciones antiguas que usaban 'get_nanoid'
get_nanoid = generate_nanoid

class CaosEpochORM(models.Model):
    """
    Representa una 'Época' o periodo temporal en la cronología del mundo.
    Se utiliza para anclaje temporal de entidades y eventos.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_year = models.IntegerField(default=0)
    end_year = models.IntegerField(null=True, blank=True)
    def __str__(self): return f"[{self.id}] {self.name}"
    class Meta: db_table = 'caos_epochs'; ordering = ['start_year']

class CaosWorldORM(models.Model):
    """
    Modelo central que representa cualquier 'Entidad' del proyecto (Mundo, Región, Ciudad, Personaje).
    Almacena tanto la jerarquía (J-ID) como la identidad pública (NanoID).
    """
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

    def save(self, *args, **kwargs):
        """Override save to validate and sanitize metadata."""
        if self.metadata:
            from src.Shared.Services.MetadataValidator import sanitize_metadata, validate_metadata
            
            # Sanitizar metadata
            self.metadata = sanitize_metadata(self.metadata)
            
            # Validar metadata (modo warning, no bloquea guardado)
            is_valid, error = validate_metadata(self.metadata, strict=False)
            if not is_valid:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Metadata validation warning for {self.id}: {error}")
        
        super().save(*args, **kwargs)

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
    """
    Almacena las diferentes propuestas y versiones de una entidad. 
    Es la base del sistema de Control de Versiones 'ECLAI'.
    
    Soporta dos tipos de propuestas:
    - LIVE: Cambios a la versión actual de la entidad
    - TIMELINE: Snapshots históricos/temporales
    """
    world = models.ForeignKey(CaosWorldORM, on_delete=models.CASCADE, related_name='versiones')
    
    # Campos para propuestas LIVE (versión actual)
    proposed_name = models.CharField(max_length=150)
    proposed_description = models.TextField(null=True, blank=True)
    
    # Metadatos de la propuesta
    version_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default="PENDING")  # PENDING, APPROVED, REJECTED, LIVE
    change_log = models.CharField(max_length=255, blank=True)
    cambios = models.JSONField(default=dict, blank=True)
    
    # NUEVO: Tipo de cambio
    CHANGE_TYPE_CHOICES = [
        ('LIVE', 'Cambio en versión actual'),
        ('TIMELINE', 'Snapshot temporal'),
        ('METADATA', 'Solo metadata')
    ]
    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPE_CHOICES,
        default='LIVE',
        help_text='Tipo de cambio propuesto'
    )
    
    # NUEVO: Campos para propuestas TIMELINE
    timeline_year = models.IntegerField(
        null=True,
        blank=True,
        help_text='Año del snapshot temporal (solo para change_type=TIMELINE)'
    )
    proposed_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text='Snapshot temporal completo: {description, metadata, images, cover_image}'
    )
    
    # Campos de revisión
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='proposed_variants')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_variants')
    admin_feedback = models.TextField(blank=True)
    
    class Meta: 
        db_table = 'caos_versions'
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['change_type', 'status'], name='idx_change_type_status'),
            models.Index(fields=['timeline_year'], name='idx_timeline_year'),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(change_type='TIMELINE', timeline_year__isnull=False) |
                    models.Q(change_type__in=['LIVE', 'METADATA'], timeline_year__isnull=True)
                ),
                name='timeline_year_required_for_timeline'
            ),
            models.CheckConstraint(
                check=(
                    models.Q(change_type='TIMELINE', proposed_snapshot__isnull=False) |
                    models.Q(change_type__in=['LIVE', 'METADATA'])
                ),
                name='proposed_snapshot_required_for_timeline'
            ),
        ]
    
    def is_timeline_proposal(self):
        """Retorna True si es una propuesta de snapshot temporal."""
        return self.change_type == 'TIMELINE'
    
    def is_live_proposal(self):
        """Retorna True si es una propuesta de versión actual."""
        return self.change_type == 'LIVE'
    
    def get_display_title(self):
        """Retorna título descriptivo según el tipo de propuesta."""
        if self.is_timeline_proposal():
            return f"Snapshot año {self.timeline_year}: {self.world.name}"
        else:
            return f"v{self.version_number}: {self.proposed_name}"
    
    def __str__(self):
        if self.is_timeline_proposal():
            return f"[TIMELINE {self.timeline_year}] {self.world.name} - {self.status}"
        return f"[v{self.version_number}] {self.world.name} - {self.status}"


class CaosNarrativeORM(models.Model):
    """
    Almacena relatos, historias y lore asociado a una entidad. 
    Sigue una dependencia existencial: si la entidad muere, su narrativa también.
    """
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
    
    # RELACIÓN CON LÍNEA TEMPORAL
    timeline_period = models.ForeignKey(
        'TimelinePeriod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='narratives',
        help_text='Período al que pertenece esta narrativa (nulo = ACTUAL)'
    )

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
    status = models.CharField(max_length=30, default="PENDING") # PENDING, APPROVED, REJECTED, LIVE, ARCHIVED, DRAFT
    action = models.CharField(max_length=20, default="EDIT", choices=[('ADD', 'Crear'), ('EDIT', 'Editar'), ('DELETE', 'Borrar')])
    change_log = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='proposed_versions')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_versions')
    admin_feedback = models.TextField(blank=True)
    
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
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='proposed_images')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_images')
    created_at = models.DateTimeField(auto_now_add=True)
    admin_feedback = models.TextField(blank=True)

    # RELACIÓN CON LÍNEA TEMPORAL
    timeline_period = models.ForeignKey(
        'TimelinePeriod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='images',
        help_text='Período al que pertenece esta imagen (nulo = ACTUAL)'
    )

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
        ('EXPLORER', 'Explorador')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='EXPLORER')
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

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.subject}"
    
    @property
    def is_read(self):
        return self.read_at is not None


# ============================================================================
# TIMELINE PERIOD MODELS - Sistema de Líneas Temporales Independientes
# ============================================================================

class TimelinePeriod(models.Model):
    """
    Representa un período en la línea temporal de una entidad.
    Puede ser el estado ACTUAL (presente) o un período histórico con título libre.
    
    Cada período es completamente independiente con:
    - Descripción propia
    - Fotos propias (via ForeignKey)
    - Narrativas propias (via ForeignKey)
    - Versiones propias (historial de cambios)
    
    Ejemplos de títulos: "Inicios", "Expansión", "Guerra Civil", "Presente"
    """
    world = models.ForeignKey(
        CaosWorldORM, 
        on_delete=models.CASCADE,
        related_name='timeline_periods',
        help_text='Entidad a la que pertenece este período'
    )
    
    title = models.CharField(
        max_length=100,
        help_text='Título del período: "Inicios", "Expansión", etc.'
    )
    
    slug = models.SlugField(
        max_length=150,
        help_text='URL-friendly: "inicios", "expansion"'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Descripción/Lore del período'
    )
    
    order = models.IntegerField(
        default=0,
        help_text='Orden de visualización (menor = primero)'
    )
    
    is_current = models.BooleanField(
        default=False,
        help_text='True si es el estado ACTUAL/presente'
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Metadatos adicionales del periodo (clima, población, etc)'
    )
    
    cover_image = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Nombre del archivo de portada'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['world', 'slug']]
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['world', 'is_current']),
            models.Index(fields=['world', 'slug']),
        ]
        verbose_name = 'Período Temporal'
        verbose_name_plural = 'Períodos Temporales'
    
    def __str__(self):
        prefix = "⭐ ACTUAL" if self.is_current else f"📜 {self.title}"
        return f"{self.world.name} - {prefix}"
    
    @property
    def current_version_number(self):
        """Número de la última versión aprobada"""
        last_approved = self.versions.filter(status='APPROVED').order_by('-version_number').first()
        return last_approved.version_number if last_approved else 0


class TimelinePeriodVersion(models.Model):
    """
    Versiones/Propuestas de cambios a un período específico.
    Cada período tiene su propio historial de versiones independiente.
    
    Flujo:
    1. Usuario propone cambio → status=PENDING
    2. Admin aprueba → status=APPROVED, actualiza TimelinePeriod
    3. Admin rechaza → status=REJECTED
    """
    period = models.ForeignKey(
        TimelinePeriod,
        on_delete=models.CASCADE,
        related_name='versions',
        help_text='Período al que pertenece esta versión'
    )
    
    version_number = models.IntegerField(
        help_text='Número de versión (V1, V2, V3...)'
    )
    
    proposed_title = models.CharField(
        max_length=100, 
        blank=True,
        help_text='Nuevo título propuesto (si cambia)'
    )
    
    proposed_description = models.TextField(
        blank=True,
        help_text='Nueva descripción propuesta'
    )

    proposed_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Nuevos metadatos propuestos'
    )

    ACTION_CHOICES = [
        ('ADD', 'Añadir'),
        ('EDIT', 'Editar'),
        ('DELETE', 'Eliminar'),
    ]

    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
        default='EDIT',
        help_text='Tipo de acción propuesta'
    )
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('APPROVED', 'Aprobada'),
        ('REJECTED', 'Rechazada'),
        ('ARCHIVED', 'Archivada'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='timeline_period_versions',
        help_text='Autor de la propuesta'
    )
    
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='reviewed_timeline_period_versions',
        help_text='Admin que revisó'
    )
    
    change_log = models.TextField(
        blank=True,
        help_text='Descripción de los cambios'
    )
    
    admin_feedback = models.TextField(
        blank=True,
        help_text='Feedback del admin (si rechazada)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = [['period', 'version_number']]
        ordering = ['-version_number']
        verbose_name = 'Versión de Período'
        verbose_name_plural = 'Versiones de Períodos'
    
    def __str__(self):
        return f"{self.period.title} v{self.version_number} ({self.status})"
