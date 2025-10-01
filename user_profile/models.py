from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    cedula = models.CharField(max_length=20, unique=True)
    selfie_photo = models.ImageField(upload_to='selfies/', null=True, blank=True)
    cedula_photo = models.ImageField(upload_to='cedulas/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"