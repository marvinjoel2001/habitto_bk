from django.db import models
from django.contrib.auth.models import User
from property.models import Property

class Guarantee(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='guarantees')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guarantees_paid')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_released = models.BooleanField(default=False)
    release_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Garantía de {self.amount} para {self.property}'
