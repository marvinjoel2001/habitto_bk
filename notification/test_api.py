from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Notification


class NotificationAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            message='Notificación de prueba',
            is_read=False
        )
        
    def test_create_notification(self):
        """Test crear notificación"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notification-list')
        data = {
            'user': self.user.id,
            'message': 'Nueva notificación',
            'is_read': False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 2)
        
    def test_list_notifications(self):
        """Test listar notificaciones"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_notification(self):
        """Test obtener notificación específica"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notification-detail', kwargs={'pk': self.notification.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Notificación de prueba')
        
    def test_update_notification(self):
        """Test actualizar notificación"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notification-detail', kwargs={'pk': self.notification.pk})
        data = {'is_read': True}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_mark_as_read_notification(self):
        """Test marcar notificación como leída"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notification-mark-as-read', kwargs={'pk': self.notification.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_delete_notification(self):
        """Test eliminar notificación"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notification-detail', kwargs={'pk': self.notification.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Notification.objects.count(), 0)