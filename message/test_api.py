from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Message


class MessageAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='senderpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@example.com',
            password='receiverpass123'
        )
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Mensaje de prueba'
        )
        
    def test_create_message(self):
        """Test crear mensaje"""
        self.client.force_authenticate(user=self.sender)
        url = reverse('message-list')
        data = {
            'sender': self.sender.id,
            'receiver': self.receiver.id,
            'content': 'Nuevo mensaje'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 2)
        
    def test_list_messages(self):
        """Test listar mensajes"""
        self.client.force_authenticate(user=self.sender)
        url = reverse('message-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_message(self):
        """Test obtener mensaje específico"""
        self.client.force_authenticate(user=self.sender)
        url = reverse('message-detail', kwargs={'pk': self.message.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Mensaje de prueba')
        
    def test_update_message(self):
        """Test actualizar mensaje"""
        self.client.force_authenticate(user=self.sender)
        url = reverse('message-detail', kwargs={'pk': self.message.pk})
        data = {'content': 'Mensaje actualizado'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_delete_message(self):
        """Test eliminar mensaje"""
        self.client.force_authenticate(user=self.sender)
        url = reverse('message-detail', kwargs={'pk': self.message.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Message.objects.count(), 0)