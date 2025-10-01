from django.db import models
from django.contrib.auth.models import User

class Property(models.Model):
    TYPE_CHOICES = (
        ('casa', 'Casa'),
        ('departamento', 'Departamento'),
        ('habitacion', 'Habitación'),
        ('anticretico', 'Anticrético'),
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_properties')
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_properties')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    guarantee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField()
    size = models.FloatField(blank=True, null=True)
    bedrooms = models.IntegerField(default=1)
    bathrooms = models.IntegerField(default=1)
    amenities = models.ManyToManyField('amenity.Amenity', blank=True)
    availability_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    accepted_payment_methods = models.ManyToManyField('paymentmethod.PaymentMethod', blank=True)

    def __str__(self):
        return f'{self.type} en {self.address} - {self.price} BOB'
