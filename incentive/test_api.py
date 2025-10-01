from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import Incentive


class IncentiveAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.incentive = Incentive.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            description='Incentivo de prueba'
        )
        
    def test_create_incentive(self):
        """Test crear incentivo"""
        self.client.force_authenticate(user=self.user)
        url = reverse('incentive-list')
        data = {
            'user': self.user.id,
            'amount': '150.00',
            'description': 'Nuevo incentivo'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Incentive.objects.count(), 2)
        
    def test_list_incentives(self):
        """Test listar incentivos"""
        self.client.force_authenticate(user=self.user)
        url = reverse('incentive-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_incentive(self):
        """Test obtener incentivo específico"""
        self.client.force_authenticate(user=self.user)
        url = reverse('incentive-detail', kwargs={'pk': self.incentive.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Incentivo de prueba')
        
    def test_update_incentive(self):
        """Test actualizar incentivo"""
        self.client.force_authenticate(user=self.user)
        url = reverse('incentive-detail', kwargs={'pk': self.incentive.pk})
        data = {'amount': '200.00'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_delete_incentive(self):
        """Test eliminar incentivo"""
        self.client.force_authenticate(user=self.user)
        url = reverse('incentive-detail', kwargs={'pk': self.incentive.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Incentive.objects.count(), 0)