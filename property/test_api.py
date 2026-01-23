from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.gis.geos import Point
from decimal import Decimal
from .models import Property
from amenity.models import Amenity
from paymentmethod.models import PaymentMethod
from matching.models import SearchProfile


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
        
        # Crear propiedad con PointField
        self.property = Property.objects.create(
            owner=self.owner,
            agent=self.agent,
            type='casa',
            address='Calle Test 123',
            location=Point(-63.1821, -17.7834),  # longitude, latitude
            price=Decimal('1500.00'),
            description='Casa de prueba',
            bedrooms=3,
            bathrooms=2
        )
        self.property.amenities.add(self.amenity)
        self.property.accepted_payment_methods.add(self.payment_method)
        
    def test_create_property(self):
        """Test crear propiedad con coordenadas"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-list')
        data = {
            'type': 'departamento',
            'address': 'Avenida Nueva 456',
            'latitude': -17.7834,
            'longitude': -63.1821,
            'price': '2000.00',
            'description': 'Departamento moderno',
            'bedrooms': 2,
            'bathrooms': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.count(), 2)
        
        # Verificar que se creó el Point correctamente
        new_property = Property.objects.get(address='Avenida Nueva 456')
        self.assertIsNotNone(new_property.location)
        self.assertEqual(new_property.latitude, -17.7834)
        self.assertEqual(new_property.longitude, -63.1821)
        
    def test_create_property_auto_zone(self):
        from zone.models import Zone
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-list')
        initial_zone_count = Zone.objects.count()

        data = {
            'type': 'departamento',
            'address': 'Avenida Sin Zona 100',
            'latitude': -16.5001,
            'longitude': -64.2001,
            'price': '2100.00',
            'description': 'Departamento nuevo',
            'bedrooms': 2,
            'bathrooms': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_property = Property.objects.get(address='Avenida Sin Zona 100')
        self.assertIsNotNone(new_property.zone)
        self.assertEqual(Zone.objects.count(), initial_zone_count + 1)

        data['address'] = 'Avenida Sin Zona 101'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        second_property = Property.objects.get(address='Avenida Sin Zona 101')
        self.assertEqual(second_property.zone_id, new_property.zone_id)
        self.assertEqual(Zone.objects.count(), initial_zone_count + 1)

    def test_create_property_with_zone_id(self):
        """Test crear propiedad con zone_id"""
        from zone.models import Zone
        zone = Zone.objects.create(
            name='Zona Test',
            bounds=Point(-63.1821, -17.7834).buffer(0.01)
        )
        
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-list')
        data = {
            'type': 'departamento',
            'address': 'Avenida Nueva 456',
            'zone_id': zone.id,
            'price': '2000.00',
            'description': 'Departamento moderno',
            'bedrooms': 2,
            'bathrooms': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        new_property = Property.objects.get(address='Avenida Nueva 456')
        self.assertEqual(new_property.zone, zone)
        
    def test_list_properties(self):
        """Test listar propiedades"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Verificar que las coordenadas se devuelven correctamente
        property_data = response.data['results'][0]
        self.assertEqual(property_data['latitude'], -17.7834)
        self.assertEqual(property_data['longitude'], -63.1821)
        
    def test_retrieve_property(self):
        """Test obtener propiedad específica"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-detail', kwargs={'pk': self.property.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], 'Calle Test 123')
        self.assertEqual(response.data['latitude'], -17.7834)
        self.assertEqual(response.data['longitude'], -63.1821)
        
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
        
    def test_map_endpoint(self):
        """Test endpoint de mapa"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-map')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'FeatureCollection')
        self.assertEqual(len(response.data['features']), 1)
        
    def test_map_endpoint_with_location_filter(self):
        """Test endpoint de mapa con filtro de ubicación"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-map')
        response = self.client.get(url, {
            'lat': -17.7834,
            'lng': -63.1821,
            'radius': 5
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['features']), 1)
        
    def test_nearby_properties(self):
        """Test propiedades cercanas"""
        # Crear otra propiedad cercana
        nearby_property = Property.objects.create(
            owner=self.owner,
            type='departamento',
            address='Calle Cercana 789',
            location=Point(-63.1825, -17.7838),  # Muy cerca
            price=Decimal('1200.00'),
            description='Departamento cercano',
            bedrooms=2,
            bathrooms=1
        )
        
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-nearby', kwargs={'pk': self.property.pk})
        response = self.client.get(url, {'radius': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], nearby_property.id)

    def test_back_event_and_stats(self):
        # Registrar vista y back
        self.client.force_authenticate(user=self.owner)
        view_url = reverse('property-view', kwargs={'pk': self.property.pk})
        back_url = reverse('property-back', kwargs={'pk': self.property.pk})
        self.client.post(view_url)
        self.client.post(back_url)
        stats_url = reverse('property-interaction-stats')
        resp = self.client.get(stats_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        counts = resp.data.get('counts', {})
        self.assertGreaterEqual(counts.get('views', 0), 1)
        self.assertGreaterEqual(counts.get('back', 0), 1)

    def test_match_listing_excludes_own_by_default(self):
        self.client.force_authenticate(user=self.owner)
        SearchProfile.objects.create(user=self.owner)
        url = reverse('property-list')
        response = self.client.get(url, {
            'match_score': 0,
            'order_by_match': 'true',
            'page': 1,
            'page_size': 50
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results') if isinstance(response.data, dict) else response.data
        for item in results:
            self.assertNotEqual(item.get('owner'), self.owner.id)

    def test_match_listing_include_own_when_param_true(self):
        other = User.objects.create_user(username='other_owner', email='o@example.com', password='x')
        Property.objects.create(
            owner=other,
            type='departamento',
            address='Otra Prop',
            location=Point(-63.1822, -17.7835),
            price=Decimal('1300.00'),
            description='Otra',
            bedrooms=2,
            bathrooms=1
        )
        self.client.force_authenticate(user=self.owner)
        SearchProfile.objects.create(user=self.owner)
        url = reverse('property-list')
        response = self.client.get(url, {
            'match_score': 0,
            'order_by_match': 'true',
            'include_own': 'true',
            'page': 1,
            'page_size': 50
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results') if isinstance(response.data, dict) else response.data
        owners = {item.get('owner') for item in results}
        self.assertIn(self.owner.id, owners)
