from django.db import models
from property.models import Property

class Photo(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='photos')
    image_url = models.URLField(max_length=500, blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Foto de {self.property.address}'