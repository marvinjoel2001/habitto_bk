from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('inquilino', 'Inquilino'),
        ('propietario', 'Propietario'),
        ('agente', 'Agente'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='inquilino')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    favorites = models.ManyToManyField('property.Property', related_name='favorited_by', blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
