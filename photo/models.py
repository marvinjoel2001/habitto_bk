from django.db import models
from property.models import Property

class Photo(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='properties/')
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Foto de {self.property.address}'