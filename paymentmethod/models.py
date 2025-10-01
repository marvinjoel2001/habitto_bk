from django.db import models
from django.contrib.auth.models import User

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods', null=True, blank=True)

    def __str__(self):
        return self.name
