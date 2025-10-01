from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from .models import PaymentMethod


class PaymentMethodAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.payment_method = PaymentMethod.objects.create(
            name='Efectivo'
        )
        
    def test_create_payment_method(self):
        """Test crear método de pago"""
        self.client.force_authenticate(user=self.user)
        url = reverse('paymentmethod-list')
        data = {
            'name': 'Tarjeta de Crédito'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PaymentMethod.objects.count(), 2)
        
    def test_list_payment_methods(self):
        """Test listar métodos de pago"""
        self.client.force_authenticate(user=self.user)
        url = reverse('paymentmethod-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_payment_method(self):
        """Test obtener método de pago específico"""
        self.client.force_authenticate(user=self.user)
        url = reverse('paymentmethod-detail', kwargs={'pk': self.payment_method.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Efectivo')
        
    def test_update_payment_method(self):
        """Test actualizar método de pago"""
        self.client.force_authenticate(user=self.user)
        url = reverse('paymentmethod-detail', kwargs={'pk': self.payment_method.pk})
        data = {'name': 'Transferencia Bancaria'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_delete_payment_method(self):
        """Test eliminar método de pago"""
        self.client.force_authenticate(user=self.user)
        url = reverse('paymentmethod-detail', kwargs={'pk': self.payment_method.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PaymentMethod.objects.count(), 0)