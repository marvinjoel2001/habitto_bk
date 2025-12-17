from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db import models
import uuid
import os
from datetime import datetime

def user_profile_picture_path(instance, filename):
    """
    Genera un nombre único para la foto de perfil incluyendo:
    - ID del usuario
    - Timestamp
    - UUID para garantizar unicidad
    - Extensión original
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    # Soporta tanto UserProfile como ProfilePictureHistory (que tienen user_profile)
    user_obj = getattr(instance, 'user', None)
    if user_obj is None and hasattr(instance, 'user_profile'):
        user_obj = instance.user_profile.user
    user_id = user_obj.id if user_obj else 'unknown'
    new_filename = f"user_{user_id}_{timestamp}_{unique_id}.{ext}"
    return os.path.join('profile_pictures', new_filename)

def verification_document_path(instance, filename):
    """
    Ruta para almacenar documentos de verificación (CI/Pasaporte y selfie).
    Incluye ID de usuario, timestamp y UUID para unicidad.
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    user_obj = getattr(instance, 'user', None)
    user_id = user_obj.id if user_obj else 'unknown'
    new_filename = f"verify_{user_id}_{timestamp}_{unique_id}.{ext}"
    return os.path.join('verification_docs', new_filename)

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('inquilino', 'Inquilino'),
        ('propietario', 'Propietario'),
        ('agente', 'Agente'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='inquilino')
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture_url = models.URLField(max_length=500, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    # Campos de verificación automática
    id_card_front_url = models.URLField(max_length=500, blank=True, null=True)
    id_card_back_url = models.URLField(max_length=500, blank=True, null=True)
    selfie_url = models.URLField(max_length=500, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)
    # Eliminación diferida de cuenta
    deletion_pending = models.BooleanField(default=False)
    deletion_requested_at = models.DateTimeField(blank=True, null=True)
    deletion_scheduled_for = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    favorites = models.ManyToManyField('property.Property', related_name='favorited_by', blank=True)

    # Campos para agentes/roomies
    is_agent = models.BooleanField(default=False)
    agent_commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)
    roommate_vibes = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class ProfilePictureHistory(models.Model):
    """
    Modelo para mantener historial de fotos de perfil
    """
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='picture_history')
    image_url = models.URLField(max_length=500, blank=True, null=True)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.uploaded_at}"


class Block(models.Model):
    """
    Relación de bloqueo entre usuarios. Si A bloquea a B, se debe evitar interacción y visibilidad en ambos sentidos.
    """
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_made')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')
        indexes = [
            models.Index(fields=['blocker', 'blocked']),
        ]

    def __str__(self):
        return f"{self.blocker.username} bloqueó a {self.blocked.username}"


class UserLocationPoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_points')
    location = gis_models.PointField(srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user_id}@{self.created_at} ({self.location.y},{self.location.x})"
