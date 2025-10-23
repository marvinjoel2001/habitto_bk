from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from property.models import Property
from amenity.models import Amenity
from paymentmethod.models import PaymentMethod
from user.models import UserProfile
from photo.models import Photo
from message.models import Message
from notification.models import Notification
from payment.models import Payment
from guarantee.models import Guarantee
from review.models import Review
from incentive.models import Incentive
from django.core.files.uploadedfile import SimpleUploadedFile


class APIIntegrationTestCase(APITestCase):
    """Tests de integración para verificar flujos completos de la API"""
    
    def setUp(self):
        """Configuración inicial para los tests de integración"""
        # Crear usuarios
        self.propietario = User.objects.create_user(
            username='propietario',
            email='propietario@example.com',
            password='proppass123',
            first_name='Juan',
            last_name='Propietario'
        )
        
        self.inquilino = User.objects.create_user(
            username='inquilino',
            email='inquilino@example.com',
            password='inqupass123',
            first_name='María',
            last_name='Inquilino'
        )
        
        # Crear perfiles
        self.perfil_propietario = UserProfile.objects.create(
            user=self.propietario,
            user_type='propietario',
            phone='+59112345678',
            is_verified=True
        )
        
        self.perfil_inquilino = UserProfile.objects.create(
            user=self.inquilino,
            user_type='inquilino',
            phone='+59187654321',
            is_verified=True
        )
        
    def test_complete_rental_flow(self):
        """Test del flujo completo de alquiler"""
        
        # 1. Propietario se autentica
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'propietario',
            'password': 'proppass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        propietario_token = login_response.data['access']
        
        # 2. Crear amenidades
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {propietario_token}')
        amenity_url = reverse('amenity-list')
        amenity_data = {'name': 'Piscina'}
        amenity_response = self.client.post(amenity_url, amenity_data, format='json')
        amenity_id = amenity_response.data['id']
        
        # 3. Crear método de pago
        payment_method_url = reverse('paymentmethod-list')
        payment_method_data = {'name': 'Efectivo'}
        payment_method_response = self.client.post(payment_method_url, payment_method_data, format='json')
        payment_method_id = payment_method_response.data['id']
        
        # 4. Propietario crea propiedad
        property_url = reverse('property-list')
        property_data = {
            'owner': self.propietario.id,
            'type': 'casa',
            'address': 'Calle Principal 123, La Paz',
            'latitude': '-16.500000',
            'longitude': '-68.150000',
            'price': '1200.00',
            'guarantee': '1200.00',
            'description': 'Casa amplia en zona residencial',
            'size': 150.5,
            'bedrooms': 3,
            'bathrooms': 2,
            'amenities': [amenity_id],
            'availability_date': '2025-11-01',
            'accepted_payment_methods': [payment_method_id]
        }
        property_response = self.client.post(property_url, property_data, format='json')
        self.assertEqual(property_response.status_code, status.HTTP_201_CREATED)
        property_id = property_response.data['id']
        
        # 5. Subir foto de la propiedad
        photo_url = reverse('photo-list')
        test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9',
            content_type='image/jpeg'
        )
        photo_data = {
            'property': property_id,
            'image': test_image,
            'caption': 'Fachada principal'
        }
        photo_response = self.client.post(photo_url, photo_data, format='multipart')
        self.assertEqual(photo_response.status_code, status.HTTP_201_CREATED)
        
        # 6. Inquilino se autentica
        login_data = {
            'username': 'inquilino',
            'password': 'inqupass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        inquilino_token = login_response.data['access']
        
        # 7. Inquilino busca propiedades
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {inquilino_token}')
        search_response = self.client.get(property_url, {'search': 'Principal'})
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(search_response.data['results']), 1)
        
        # 8. Inquilino agrega propiedad a favoritos
        profile_url = reverse('userprofile-detail', kwargs={'pk': self.perfil_inquilino.pk})
        favorites_data = {'favorites': [property_id]}
        favorites_response = self.client.patch(profile_url, favorites_data, format='json')
        self.assertEqual(favorites_response.status_code, status.HTTP_200_OK)
        
        # 9. Inquilino envía mensaje al propietario
        message_url = reverse('message-list')
        message_data = {
            'sender': self.inquilino.id,
            'receiver': self.propietario.id,
            'content': 'Hola, estoy interesado en tu propiedad en Calle Principal 123'
        }
        message_response = self.client.post(message_url, message_data, format='json')
        self.assertEqual(message_response.status_code, status.HTTP_201_CREATED)
        
        # 10. Propietario responde
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {propietario_token}')
        response_data = {
            'sender': self.propietario.id,
            'receiver': self.inquilino.id,
            'content': '¡Hola! Sí, la propiedad está disponible. ¿Te gustaría visitarla?'
        }
        response_message = self.client.post(message_url, response_data, format='json')
        self.assertEqual(response_message.status_code, status.HTTP_201_CREATED)
        
        # 11. Crear garantía
        guarantee_url = reverse('guarantee-list')
        guarantee_data = {
            'property': property_id,
            'tenant': self.inquilino.id,
            'amount': '1200.00'
        }
        guarantee_response = self.client.post(guarantee_url, guarantee_data, format='json')
        self.assertEqual(guarantee_response.status_code, status.HTTP_201_CREATED)
        guarantee_id = guarantee_response.data['id']
        
        # 12. Crear pago
        payment_url = reverse('payment-list')
        payment_data = {
            'property': property_id,
            'tenant': self.inquilino.id,
            'amount': '1200.00',
            'due_date': '2025-11-01',
            'method': payment_method_id
        }
        payment_response = self.client.post(payment_url, payment_data, format='json')
        self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED)
        payment_id = payment_response.data['id']
        
        # 13. Marcar pago como pagado
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {inquilino_token}')
        payment_update_data = {
            'status': 'pagado',
            'paid_date': '2025-10-30'
        }
        payment_detail_url = reverse('payment-detail', kwargs={'pk': payment_id})
        payment_update_response = self.client.patch(payment_detail_url, payment_update_data, format='json')
        self.assertEqual(payment_update_response.status_code, status.HTTP_200_OK)
        
        # 14. Liberar garantía (al final del contrato)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {propietario_token}')
        release_url = reverse('guarantee-release', kwargs={'pk': guarantee_id})
        release_response = self.client.post(release_url)
        self.assertEqual(release_response.status_code, status.HTTP_200_OK)
        
        # 15. Inquilino deja reseña
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {inquilino_token}')
        review_url = reverse('review-list')
        review_data = {
            'property': property_id,
            'user': self.inquilino.id,
            'rating': 5,
            'comment': 'Excelente propiedad, muy bien ubicada y en perfecto estado'
        }
        review_response = self.client.post(review_url, review_data, format='json')
        self.assertEqual(review_response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que todo se creó correctamente
        self.assertEqual(Property.objects.count(), 1)
        self.assertEqual(Photo.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 2)
        self.assertEqual(Guarantee.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Review.objects.count(), 1)
        
    def test_pagination_on_all_endpoints(self):
        """Test que todos los endpoints de listado soporten paginación"""
        # Autenticar usuario
        self.client.force_authenticate(user=self.propietario)
        
        endpoints_to_test = [
            'user-list',
            'userprofile-list',
            'property-list',
            'photo-list',
            'amenity-list',
            'guarantee-list',
            'incentive-list',
            'payment-list',
            'paymentmethod-list',
            'review-list',
            'notification-list',
            'message-list'
        ]
        
        for endpoint_name in endpoints_to_test:
            with self.subTest(endpoint=endpoint_name):
                url = reverse(endpoint_name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # Verificar estructura de paginación
                self.assertIn('count', response.data)
                self.assertIn('results', response.data)
                # next y previous pueden ser null
                self.assertIn('next', response.data)
                self.assertIn('previous', response.data)
                
    def test_filtering_capabilities(self):
        """Test capacidades de filtrado en endpoints que lo soportan"""
        self.client.force_authenticate(user=self.propietario)
        
        # Crear datos de prueba
        amenity = Amenity.objects.create(name='Piscina')
        payment_method = PaymentMethod.objects.create(name='Efectivo')
        
        property1 = Property.objects.create(
            owner=self.propietario,
            type='casa',
            address='Casa en zona norte',
            price=Decimal('1500.00'),
            description='Casa amplia',
            bedrooms=3,
            bathrooms=2,
            is_active=True
        )
        
        property2 = Property.objects.create(
            owner=self.propietario,
            type='departamento',
            address='Departamento en zona sur',
            price=Decimal('800.00'),
            description='Departamento moderno',
            bedrooms=2,
            bathrooms=1,
            is_active=False
        )
        
        # Test filtros en propiedades
        property_url = reverse('property-list')
        
        # Filtrar por tipo
        response = self.client.get(property_url, {'type': 'casa'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['type'], 'casa')
        
        # Filtrar por estado activo
        response = self.client.get(property_url, {'is_active': 'true'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['is_active'], True)
        
        # Búsqueda por texto
        response = self.client.get(property_url, {'search': 'norte'})
        self.assertEqual(len(response.data['results']), 1)
        
        # Ordenamiento
        response = self.client.get(property_url, {'ordering': 'price'})
        self.assertEqual(len(response.data['results']), 2)
        # El más barato debería estar primero
        self.assertEqual(float(response.data['results'][0]['price']), 800.00)
        
    def test_authentication_required_endpoints(self):
        """Test que los endpoints que requieren autenticación la validen correctamente"""
        protected_endpoints = [
            ('user-list', 'get'),
            ('userprofile-list', 'get'),
            ('property-list', 'get'),
            ('photo-list', 'get'),
            ('amenity-list', 'get'),
            ('guarantee-list', 'get'),
            ('incentive-list', 'get'),
            ('payment-list', 'get'),
            ('paymentmethod-list', 'get'),
            ('review-list', 'get'),
            ('notification-list', 'get'),
            ('message-list', 'get')
        ]
        
        for endpoint_name, method in protected_endpoints:
            with self.subTest(endpoint=endpoint_name, method=method):
                url = reverse(endpoint_name)
                if method == 'get':
                    response = self.client.get(url)
                elif method == 'post':
                    response = self.client.post(url, {})
                
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)