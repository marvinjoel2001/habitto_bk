from django.db import models
from django.contrib.auth.models import User

class Incentive(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incentives')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Incentivo de {self.amount} para {self.user}'