from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from .models import Photo
from property.models import Property
import tempfile
import os

class PhotoAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.property = Property.objects.create(
            owner=self.user,
            type='casa',
            address='Calle Test 123',
            price=Decimal('1500.00'),
            description='Casa de prueba',
            bedrooms=3,
            bathrooms=2
        )
        
        # Crear imagen de prueba más realista
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=self.create_test_image_content(),
            content_type='image/jpeg'
        )
        
        self.photo = Photo.objects.create(
            property=self.property,
            image=self.test_image,
            caption='Foto de prueba'
        )
    
    def create_test_image_content(self):
        """Crear contenido de imagen más realista para las pruebas"""
        # Crear un archivo de imagen simple pero válido
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        
    def test_create_photo(self):
        """Test crear foto"""
        self.client.force_authenticate(user=self.user)
        url = reverse('photo-list')
        
        # Crear nueva imagen para el test
        new_image = SimpleUploadedFile(
            name='new_image.jpg',
            content=self.create_test_image_content(),
            content_type='image/jpeg'
        )
        
        data = {
            'property': self.property.id,
            'image': new_image,
            'caption': 'Nueva foto'
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Photo.objects.count(), 2)
        
    def test_list_photos(self):
        """Test listar fotos"""
        self.client.force_authenticate(user=self.user)
        url = reverse('photo-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_photo(self):
        """Test obtener foto específica"""
        self.client.force_authenticate(user=self.user)
        url = reverse('photo-detail', kwargs={'pk': self.photo.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['caption'], 'Foto de prueba')
        
    def test_update_photo(self):
        """Test actualizar foto"""
        self.client.force_authenticate(user=self.user)
        url = reverse('photo-detail', kwargs={'pk': self.photo.pk})
        data = {'caption': 'Foto actualizada'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_delete_photo(self):
        """Test eliminar foto"""
        self.client.force_authenticate(user=self.user)
        url = reverse('photo-detail', kwargs={'pk': self.photo.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Photo.objects.count(), 0)