from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta
from .models import Payment
from property.models import Property
from paymentmethod.models import PaymentMethod


class PaymentAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='ownerpass123'
        )
        self.tenant = User.objects.create_user(
            username='tenant',
            email='tenant@example.com',
            password='tenantpass123'
        )
        
        self.property = Property.objects.create(
            owner=self.owner,
            type='casa',
            address='Calle Test 123',
            price=Decimal('1500.00'),
            description='Casa de prueba',
            bedrooms=3,
            bathrooms=2
        )
        
        self.payment_method = PaymentMethod.objects.create(name='Transferencia')
        
        self.payment = Payment.objects.create(
            property=self.property,
            tenant=self.tenant,
            amount=Decimal('1500.00'),
            status='pendiente',
            due_date=date.today() + timedelta(days=30),
            method=self.payment_method
        )
        
    def test_create_payment(self):
        """Test crear pago"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('payment-list')
        data = {
            'property': self.property.id,
            'tenant': self.tenant.id,
            'amount': '2000.00',
            'status': 'pendiente',
            'due_date': (date.today() + timedelta(days=30)).isoformat(),
            'method': self.payment_method.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 2)
        
    def test_list_payments(self):
        """Test listar pagos"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('payment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_payment(self):
        """Test obtener pago específico"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('payment-detail', kwargs={'pk': self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pendiente')
        
    def test_update_payment(self):
        """Test actualizar pago"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('payment-detail', kwargs={'pk': self.payment.pk})
        data = {'status': 'pagado'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_delete_payment(self):
        """Test eliminar pago"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('payment-detail', kwargs={'pk': self.payment.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Payment.objects.count(), 0)