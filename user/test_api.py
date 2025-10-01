from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile


class UserAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
    def test_create_user(self):
        """Test crear usuario - debe ser público"""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        # No autenticar - el registro debe ser público
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        
    def test_list_users(self):
        """Test listar usuarios"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_user(self):
        """Test obtener usuario específico"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-detail', kwargs={'pk': self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        
    def test_update_user(self):
        """Test actualizar usuario"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-detail', kwargs={'pk': self.user.pk})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        
    def test_delete_user(self):
        """Test eliminar usuario"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-detail', kwargs={'pk': self.user.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 1)


class UserProfileAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            user_type='inquilino',
            phone='12345678',
            is_verified=False
        )
        
    def test_create_user_profile(self):
        """Test crear perfil de usuario"""
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='newpass123'
        )
        self.client.force_authenticate(user=new_user)
        url = reverse('userprofile-list')
        data = {
            'user_type': 'propietario',
            'phone': '87654321'
        }
        # No enviar user_id - se asigna automáticamente en la vista
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.count(), 2)
        
    def test_list_user_profiles(self):
        """Test listar perfiles de usuario"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_user_profile(self):
        """Test obtener perfil específico"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_type'], 'inquilino')
        
    def test_update_user_profile(self):
        """Test actualizar perfil"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.pk})
        data = {'phone': '99999999'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, '99999999')
        
    def test_verify_user_profile(self):
        """Test verificar perfil de usuario"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userprofile-verify', kwargs={'pk': self.profile.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_verified)
        
    def test_delete_user_profile(self):
        """Test eliminar perfil"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserProfile.objects.count(), 0)