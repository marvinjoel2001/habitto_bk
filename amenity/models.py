from django.db import models

class Amenity(models.Model):
    name = models.CharField(max_length=100)  # Ej., 'Garaje', 'Piscina', 'Amueblado'

    def __str__(self):
        return self.name
