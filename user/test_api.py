from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import UserProfile
from .models import Block
import unittest


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

    @unittest.mock.patch('bk_habitto.services.cloudinary_service.CloudinaryService.upload_image')
    def test_submit_verification_marks_verified(self, mock_upload):
        """Test verificación automática con documentos y selfie"""
        mock_upload.return_value = 'http://cloudinary.com/test.jpg'
        self.client.force_authenticate(user=self.user)
        url = reverse('userprofile-submit-verification')
        front = SimpleUploadedFile('front.jpg', b'front', content_type='image/jpeg')
        back = SimpleUploadedFile('back.jpg', b'back', content_type='image/jpeg')
        selfie = SimpleUploadedFile('selfie.jpg', b'selfie', content_type='image/jpeg')
        data = {
            'id_front': front,
            'id_back': back,
            'selfie': selfie,
            'document_number': 'CI-1234567'
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('is_verified'))


    def test_block_user_prevents_profile_access_and_messages(self):
        other = User.objects.create_user(username='other', email='o@example.com', password='x')
        # crear perfiles
        UserProfile.objects.create(user=other)
        self.client.force_authenticate(user=self.user)
        # bloquear
        resp = self.client.post(reverse('userprofile-block'), {'other_user_id': other.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # acceso a perfil bloqueado
        resp2 = self.client.get(reverse('userprofile-by-user', kwargs={'user_id': other.id}))
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)
        # enviar mensaje
        from message.models import Message
        self.client.force_authenticate(user=self.user)
        resp3 = self.client.post(reverse('message-list'), {'sender': self.user.id, 'receiver': other.id, 'content': 'Hola'}, format='json')
        self.assertEqual(resp3.status_code, status.HTTP_403_FORBIDDEN)

    def test_block_user_filters_properties(self):
        other = User.objects.create_user(username='ownerB', email='b@example.com', password='x')
        from property.models import Property
        from django.contrib.gis.geos import Point
        from decimal import Decimal
        Property.objects.create(owner=other, type='casa', address='Block St', location=Point(-63.1821, -17.7834), price=Decimal('1000.00'), description='X', bedrooms=1, bathrooms=1)
        self.client.force_authenticate(user=self.user)
        # bloquear
        self.client.post(reverse('userprofile-block'), {'other_user_id': other.id}, format='json')
        # listar propiedades, debe excluir del owner bloqueado
        resp = self.client.get(reverse('property-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data.get('results') if isinstance(resp.data, dict) else resp.data
        for item in results:
            self.assertNotEqual(item.get('owner'), other.id)

    def test_request_and_cancel_delete_account(self):
        self.client.force_authenticate(user=self.user)
        url_req = reverse('userprofile-request-delete-account')
        resp = self.client.post(url_req)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        from user.models import UserProfile
        prof = UserProfile.objects.get(user=self.user)
        self.assertTrue(prof.deletion_pending)
        self.assertIsNotNone(prof.deletion_scheduled_for)
        # Cancelar
        url_cancel = reverse('userprofile-cancel-delete-account')
        resp2 = self.client.post(url_cancel)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        prof.refresh_from_db()
        self.assertFalse(prof.deletion_pending)
        self.assertIsNone(prof.deletion_scheduled_for)

    def test_login_cancels_deletion(self):
        # Marcar eliminación
        from user.models import UserProfile
        prof = UserProfile.objects.get(user=self.user)
        from django.utils import timezone
        prof.deletion_pending = True
        prof.deletion_requested_at = timezone.now()
        prof.deletion_scheduled_for = timezone.now()
        prof.save(update_fields=['deletion_pending', 'deletion_requested_at', 'deletion_scheduled_for'])
        # Login
        url = reverse('token_obtain_pair')
        resp = self.client.post(url, {'username': 'testuser', 'password': 'testpass123'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        prof.refresh_from_db()
        self.assertFalse(prof.deletion_pending)

    def test_location_submit_and_route(self):
        from django.contrib.gis.geos import Point
        from user.models import UserLocationPoint
        self.client.force_authenticate(user=self.user)
        # Enviar 3 puntos
        url_submit = '/api/location_points/submit/'
        self.client.post(url_submit, {'latitude': -17.7834, 'longitude': -63.1821}, format='json')
        self.client.post(url_submit, {'latitude': -17.7840, 'longitude': -63.1830}, format='json')
        self.client.post(url_submit, {'latitude': -17.7850, 'longitude': -63.1840}, format='json')
        # Ruta diaria
        url_route = '/api/location_points/route/?period=day'
        resp = self.client.get(url_route)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data.get('count', 0), 3)

    def test_delete_user_profile(self):
        """Test eliminar perfil"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserProfile.objects.count(), 0)
