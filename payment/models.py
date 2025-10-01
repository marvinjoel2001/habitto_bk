from django.db import models
from django.contrib.auth.models import User
from property.models import Property

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('retrasado', 'Retrasado'),
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payments')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_made')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    method = models.ForeignKey('paymentmethod.PaymentMethod', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'Pago de {self.amount} para {self.property}'
