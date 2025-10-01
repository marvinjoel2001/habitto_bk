from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import Guarantee
from property.models import Property


class GuaranteeAPITestCase(APITestCase):
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
        
        self.guarantee = Guarantee.objects.create(
            property=self.property,
            tenant=self.tenant,
            amount=Decimal('300.00'),
            is_released=False
        )
        
    def test_create_guarantee(self):
        """Test crear garantía"""
        new_tenant = User.objects.create_user(
            username='newtenant',
            email='newtenant@example.com',
            password='newpass123'
        )
        self.client.force_authenticate(user=self.owner)
        url = reverse('guarantee-list')
        data = {
            'property': self.property.id,
            'tenant': new_tenant.id,
            'amount': '500.00',
            'is_released': False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Guarantee.objects.count(), 2)
        
    def test_list_guarantees(self):
        """Test listar garantías"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('guarantee-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_guarantee(self):
        """Test obtener garantía específica"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('guarantee-detail', kwargs={'pk': self.guarantee.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_released'], False)
        
    def test_update_guarantee(self):
        """Test actualizar garantía"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('guarantee-detail', kwargs={'pk': self.guarantee.pk})
        data = {'amount': '400.00'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_release_guarantee(self):
        """Test liberar garantía"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('guarantee-release', kwargs={'pk': self.guarantee.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_delete_guarantee(self):
        """Test eliminar garantía"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('guarantee-detail', kwargs={'pk': self.guarantee.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Guarantee.objects.count(), 0)