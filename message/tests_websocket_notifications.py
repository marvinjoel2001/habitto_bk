import json
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TransactionTestCase
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from message.notification_consumers import PropertyNotificationConsumer, TenantNotificationConsumer, send_property_like_notification, send_match_accepted_notification
from message.routing import websocket_urlpatterns
from property.models import Property
from matching.models import Match
from datetime import datetime
import asyncio


class WebSocketNotificationTests(TransactionTestCase):
    
    def setUp(self):
        # Crear usuarios de prueba
        self.owner = User.objects.create_user(
            username='test_owner',
            email='owner@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Owner'
        )
        
        self.tenant = User.objects.create_user(
            username='test_tenant',
            email='tenant@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Tenant'
        )
        
        # Crear propiedad de prueba
        from django.contrib.gis.geos import Point
        self.property = Property.objects.create(
            owner=self.owner,
            type='departamento',
            address='Test Address 123',
            price=1000.00,
            bedrooms=2,
            description='Test property description',
            location=Point(-68.15, -16.5)  # longitude, latitude
        )
        
        self.channel_layer = get_channel_layer()
    
    async def test_property_notification_consumer_connection(self):
        """Test de conexión al consumer de notificaciones de propiedad"""
        communicator = WebsocketCommunicator(
            PropertyNotificationConsumer.as_asgi(),
            f"/ws/property-notifications/{self.owner.id}/"
        )
        
        # Simular usuario autenticado
        communicator.scope['user'] = self.owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Verificar mensaje de conexión
        response = await communicator.receive_from()
        response_data = json.loads(response)
        self.assertEqual(response_data['type'], 'connection_established')
        self.assertEqual(response_data['message'], 'Conectado a notificaciones de propiedades')
        
        await communicator.disconnect()
    
    async def test_property_notification_consumer_unauthorized(self):
        """Test de conexión no autorizada"""
        communicator = WebsocketCommunicator(
            PropertyNotificationConsumer.as_asgi(),
            f"/ws/property-notifications/{self.owner.id}/"
        )
        
        # Usuario no autenticado
        communicator.scope['user'] = None
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)  # Debería rechazar la conexión
    
    async def test_property_notification_consumer_wrong_user(self):
        """Test de conexión con usuario incorrecto"""
        communicator = WebsocketCommunicator(
            PropertyNotificationConsumer.as_asgi(),
            f"/ws/property-notifications/{self.owner.id}/"
        )
        
        # Usuario intentando conectarse al canal de otro usuario
        communicator.scope['user'] = self.tenant
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)  # Debería rechazar la conexión
    
    async def test_property_like_notification(self):
        """Test de notificación de like en propiedad"""
        # Conectar owner al canal de notificaciones
        owner_communicator = WebsocketCommunicator(
            PropertyNotificationConsumer.as_asgi(),
            f"/ws/property-notifications/{self.owner.id}/"
        )
        owner_communicator.scope['user'] = self.owner
        
        connected, subprotocol = await owner_communicator.connect()
        self.assertTrue(connected)
        
        # Saltar mensaje de conexión
        await owner_communicator.receive_from()
        
        # Enviar notificación de like
        interested_user_data = {
            'id': self.tenant.id,
            'username': self.tenant.username,
            'email': self.tenant.email,
            'first_name': self.tenant.first_name,
            'last_name': self.tenant.last_name
        }
        
        await send_property_like_notification(
            self.channel_layer,
            self.owner.id,
            self.property.id,
            f"{self.property.type} en {self.property.address}",
            interested_user_data
        )
        
        # Verificar que el owner reciba la notificación
        response = await owner_communicator.receive_from()
        response_data = json.loads(response)
        
        self.assertEqual(response_data['type'], 'property_like')
        self.assertEqual(response_data['property_id'], self.property.id)
        self.assertEqual(response_data['property_title'], f"{self.property.type} en {self.property.address}")
        self.assertEqual(response_data['interested_user']['username'], self.tenant.username)
        self.assertIn('timestamp', response_data)
        self.assertIn('notification_id', response_data)
        
        await owner_communicator.disconnect()
    
    async def test_match_accepted_notification(self):
        """Test de notificación de match aceptado"""
        # Conectar tanto owner como tenant a sus canales respectivos
        owner_communicator = WebsocketCommunicator(
            PropertyNotificationConsumer.as_asgi(),
            f"/ws/property-notifications/{self.owner.id}/"
        )
        owner_communicator.scope['user'] = self.owner
        
        tenant_communicator = WebsocketCommunicator(
            TenantNotificationConsumer.as_asgi(),
            f"/ws/tenant-notifications/{self.tenant.id}/"
        )
        tenant_communicator.scope['user'] = self.tenant
        
        # Conectar ambos
        owner_connected, _ = await owner_communicator.connect()
        tenant_connected, _ = await tenant_communicator.connect()
        
        self.assertTrue(owner_connected)
        self.assertTrue(tenant_connected)
        
        # Saltar mensajes de conexión
        await owner_communicator.receive_from()
        await tenant_communicator.receive_from()
        
        # Preparar datos
        property_data = {
            'id': self.property.id,
            'title': f"{self.property.type} en {self.property.address}",
            'address': self.property.address,
            'price': float(self.property.price)
        }
        
        owner_data = {
            'id': self.owner.id,
            'name': f"{self.owner.first_name} {self.owner.last_name}",
            'contact': {
                'email': self.owner.email,
                'phone': ''
            }
        }
        
        match_data = {
            'score': 85.5,
            'status': 'accepted'
        }
        
        # Enviar notificación
        await send_match_accepted_notification(
            self.channel_layer,
            self.tenant.id,
            property_data,
            owner_data,
            match_data
        )
        
        # Verificar que el owner reciba la notificación
        owner_response = await owner_communicator.receive_from()
        owner_data = json.loads(owner_response)
        self.assertEqual(owner_data['type'], 'match_accepted')
        self.assertEqual(owner_data['property_id'], self.property.id)
        self.assertEqual(owner_data['match_status'], 'accepted')
        self.assertIn('next_steps', owner_data)
        
        # Verificar que el tenant reciba la notificación específica
        tenant_response = await tenant_communicator.receive_from()
        tenant_data = json.loads(tenant_response)
        self.assertEqual(tenant_data['type'], 'match_accepted_by_owner')
        self.assertEqual(tenant_data['property_id'], self.property.id)
        self.assertEqual(tenant_data['owner_name'], f"{self.owner.first_name} {self.owner.last_name}")
        self.assertIn('next_steps', tenant_data)
        
        await owner_communicator.disconnect()
        await tenant_communicator.disconnect()
    
    async def test_ping_pong(self):
        """Test de ping/pong para mantener conexión activa"""
        communicator = WebsocketCommunicator(
            PropertyNotificationConsumer.as_asgi(),
            f"/ws/property-notifications/{self.owner.id}/"
        )
        communicator.scope['user'] = self.owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Saltar mensaje de conexión
        await communicator.receive_from()
        
        # Enviar ping
        await communicator.send_to(json.dumps({'type': 'ping'}))
        
        # Recibir pong
        response = await communicator.receive_from()
        response_data = json.loads(response)
        self.assertEqual(response_data['type'], 'pong')
        self.assertIn('timestamp', response_data)
        
        await communicator.disconnect()
    
    async def test_invalid_json(self):
        """Test de manejo de JSON inválido"""
        communicator = WebsocketCommunicator(
            PropertyNotificationConsumer.as_asgi(),
            f"/ws/property-notifications/{self.owner.id}/"
        )
        communicator.scope['user'] = self.owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Saltar mensaje de conexión
        await communicator.receive_from()
        
        # Enviar JSON inválido
        await communicator.send_to("invalid json")
        
        # Recibir error
        response = await communicator.receive_from()
        response_data = json.loads(response)
        self.assertEqual(response_data['type'], 'error')
        self.assertEqual(response_data['message'], 'JSON inválido')
        
        await communicator.disconnect()


class WebSocketPerformanceTests(TransactionTestCase):
    """Tests de rendimiento para WebSockets"""
    
    def setUp(self):
        # Crear múltiples usuarios para simular carga
        self.users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'test_user_{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            )
            self.users.append(user)
        
        self.channel_layer = get_channel_layer()
    
    async def test_multiple_simultaneous_connections(self):
        """Test de múltiples conexiones simultáneas"""
        communicators = []
        
        # Crear múltiples conectores
        for i, user in enumerate(self.users[:5]):  # Probar con 5 usuarios
            communicator = WebsocketCommunicator(
                PropertyNotificationConsumer.as_asgi(),
                f"/ws/property-notifications/{user.id}/"
            )
            communicator.scope['user'] = user
            communicators.append(communicator)
        
        # Conectar todos simultáneamente
        connections = []
        for communicator in communicators:
            connected, subprotocol = await communicator.connect()
            connections.append(connected)
            self.assertTrue(connected)
        
        # Verificar que todos estén conectados
        self.assertTrue(all(connections))
        
        # Desconectar todos
        for communicator in communicators:
            await communicator.disconnect()
    
    async def test_notification_broadcast_performance(self):
        """Test de rendimiento de broadcast de notificaciones"""
        communicators = []
        
        # Conectar múltiples usuarios
        for i, user in enumerate(self.users[:3]):
            communicator = WebsocketCommunicator(
                PropertyNotificationConsumer.as_asgi(),
                f"/ws/property-notifications/{user.id}/"
            )
            communicator.scope['user'] = user
            
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            
            # Saltar mensaje de conexión
            await communicator.receive_from()
            
            communicators.append(communicator)
        
        # Enviar múltiples notificaciones rápidamente
        start_time = datetime.now()
        
        for i in range(10):
            await send_property_like_notification(
                self.channel_layer,
                self.users[0].id,  # Enviar al primer usuario
                999,  # ID de propiedad de prueba
                f"Propiedad de prueba {i}",
                {
                    'id': self.users[1].id,
                    'username': self.users[1].username,
                    'email': self.users[1].email
                }
            )
        
        # Verificar que todas las notificaciones lleguen
        for communicator in communicators[:1]:  # Solo verificar el primero
            for i in range(10):
                response = await communicator.receive_from()
                response_data = json.loads(response)
                self.assertEqual(response_data['type'], 'property_like')
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Verificar que el procesamiento sea rápido (menos de 5 segundos para 10 notificaciones)
        self.assertLess(duration, 5.0)
        
        # Desconectar todos
        for communicator in communicators:
            await communicator.disconnect()