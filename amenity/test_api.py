from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Amenity


class AmenityAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.amenity = Amenity.objects.create(name='Piscina')
        
    def test_create_amenity(self):
        """Test crear amenidad"""
        self.client.force_authenticate(user=self.user)
        url = reverse('amenity-list')
        data = {'name': 'Gimnasio'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Amenity.objects.count(), 2)
        
    def test_list_amenities(self):
        """Test listar amenidades"""
        self.client.force_authenticate(user=self.user)
        url = reverse('amenity-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
    def test_retrieve_amenity(self):
        """Test obtener amenidad específica"""
        self.client.force_authenticate(user=self.user)
        url = reverse('amenity-detail', kwargs={'pk': self.amenity.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Piscina')
        
    def test_update_amenity(self):
        """Test actualizar amenidad"""
        self.client.force_authenticate(user=self.user)
        url = reverse('amenity-detail', kwargs={'pk': self.amenity.pk})
        data = {'name': 'Piscina Climatizada'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.amenity.refresh_from_db()
        self.assertEqual(self.amenity.name, 'Piscina Climatizada')
        
    def test_delete_amenity(self):
        """Test eliminar amenidad"""
        self.client.force_authenticate(user=self.user)
        url = reverse('amenity-detail', kwargs={'pk': self.amenity.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Amenity.objects.count(), 0)