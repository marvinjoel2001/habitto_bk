from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import Property
from amenity.models import Amenity
from paymentmethod.models import PaymentMethod


class PropertyAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='ownerpass123'
        )
        self.agent = User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='agentpass123'
        )
        
        self.amenity = Amenity.objects.create(name='Piscina')
        self.payment_method = PaymentMethod.objects.create(
            name='Efectivo',
            user=self.owner
        )
        
        self.property = Property.objects.create(
            owner=self.owner,
            agent=self.agent,
            type='casa',
            address='Calle Test 123',
            price=Decimal('1500.00'),
            description='Casa de prueba',
            bedrooms=3,
            bathrooms=2
        )
        self.property.amenities.add(self.amenity)
        self.property.accepted_payment_methods.add(self.payment_method)
        
    def test_create_property(self):
        """Test crear propiedad"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-list')
        data = {
            'owner': self.owner.id,
            'type': 'departamento',
            'address': 'Avenida Nueva 456',
            'price': '2000.00',
            'description': 'Departamento moderno',
            'bedrooms': 2,
            'bathrooms': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.count(), 2)
        
    def test_list_properties(self):
        """Test listar propiedades"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
    def test_retrieve_property(self):
        """Test obtener propiedad específica"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-detail', kwargs={'pk': self.property.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], 'Calle Test 123')
        
    def test_update_property(self):
        """Test actualizar propiedad"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-detail', kwargs={'pk': self.property.pk})
        data = {'price': '1800.00'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.price, Decimal('1800.00'))
        
    def test_delete_property(self):
        """Test eliminar propiedad"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-detail', kwargs={'pk': self.property.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Property.objects.count(), 0)
        
    def test_filter_properties_by_type(self):
        """Test filtrar propiedades por tipo"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-list')
        response = self.client.get(url, {'type': 'casa'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
    def test_search_properties(self):
        """Test buscar propiedades"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-list')
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)