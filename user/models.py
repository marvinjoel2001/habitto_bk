from django.contrib.auth.models import User
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
    ext = filename.split('.')[-1].lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    new_filename = f"user_{instance.user.id}_{timestamp}_{unique_id}.{ext}"
    return os.path.join('profile_pictures', new_filename)

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('inquilino', 'Inquilino'),
        ('propietario', 'Propietario'),
        ('agente', 'Agente'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='inquilino')
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=user_profile_picture_path, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
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
    image = models.ImageField(upload_to=user_profile_picture_path)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.uploaded_at}"
