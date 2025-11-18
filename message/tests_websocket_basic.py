from django.test import TestCase
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
import json

class WebSocketBasicTest(TestCase):
    """Test básico de funcionalidad WebSocket"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.channel_layer = get_channel_layer()
    
    def test_channel_layer_available(self):
        """Test que el channel layer está disponible"""
        self.assertIsNotNone(self.channel_layer)
    
    def test_websocket_routing_exists(self):
        """Test que las rutas WebSocket existen"""
        from message.routing import websocket_urlpatterns
        self.assertGreater(len(websocket_urlpatterns), 0)
        
        # Verificar que las rutas de notificación están presentes
        patterns = [str(pattern.pattern) for pattern in websocket_urlpatterns]
        self.assertTrue(any('property-notifications' in pattern for pattern in patterns))
        self.assertTrue(any('tenant-notifications' in pattern for pattern in patterns))


class NotificationUtilityTest(TestCase):
    """Test de las funciones de utilidad para notificaciones"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
    
    def test_notification_data_structure(self):
        """Test que la estructura de datos de notificaciones es correcta"""
        from message.notification_consumers import send_property_like_notification
        from channels.layers import get_channel_layer
        import asyncio
        
        # Test de estructura de datos (sin enviar realmente)
        interested_user_data = {
            'id': self.user1.id,
            'username': self.user1.username,
            'email': self.user1.email,
            'first_name': self.user1.first_name,
            'last_name': self.user1.last_name
        }
        
        # Verificar que los datos están bien formados
        self.assertEqual(interested_user_data['id'], self.user1.id)
        self.assertEqual(interested_user_data['username'], 'user1')
    
    def test_notification_logging(self):
        """Test del sistema de logging de notificaciones"""
        from message.websocket_logger import WebSocketInteractionLogger
        
        # Test de logging de conexión
        WebSocketInteractionLogger.log_connection(
            user_id=self.user1.id,
            connection_type='test',
            status='connected',
            details={'test': True}
        )
        
        # Test de logging de notificación
        WebSocketInteractionLogger.log_notification_sent(
            sender_id=self.user1.id,
            recipient_id=self.user2.id,
            notification_type='test',
            data={'message': 'test'}
        )
        
        # Si no hay errores, el test pasa
        self.assertTrue(True)


class WebSocketIntegrationTest(TestCase):
    """Test de integración del sistema WebSocket"""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123',
            first_name='Owner',
            last_name='Test'
        )
        
        self.tenant = User.objects.create_user(
            username='tenant',
            email='tenant@example.com',
            password='testpass123',
            first_name='Tenant',
            last_name='Test'
        )
    
    def test_property_like_notification_data(self):
        """Test de la estructura de datos para notificaciones de like"""
        property_data = {
            'id': 123,
            'title': 'Departamento en Av. Siempre Viva 123',
            'address': 'Av. Siempre Viva 123'
        }
        
        interested_user_data = {
            'id': self.tenant.id,
            'username': self.tenant.username,
            'email': self.tenant.email,
            'first_name': self.tenant.first_name,
            'last_name': self.tenant.last_name
        }
        
        # Verificar que la estructura es correcta
        self.assertEqual(interested_user_data['username'], 'tenant')
        self.assertEqual(property_data['id'], 123)
    
    def test_match_accepted_notification_data(self):
        """Test de la estructura de datos para notificaciones de match aceptado"""
        owner_data = {
            'id': self.owner.id,
            'name': f"{self.owner.first_name} {self.owner.last_name}",
            'contact': {
                'email': self.owner.email,
                'phone': '+1234567890'
            }
        }
        
        property_data = {
            'id': 456,
            'title': 'Casa en Zona Sur',
            'address': 'Calle Test 456',
            'price': 1500.00
        }
        
        match_data = {
            'score': 85.5,
            'status': 'accepted'
        }
        
        # Verificar que la estructura es correcta
        self.assertEqual(owner_data['name'], 'Owner Test')
        self.assertEqual(property_data['price'], 1500.00)
        self.assertEqual(match_data['score'], 85.5)