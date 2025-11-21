from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase
from rest_framework import status
from matching.models import SearchProfile, Match
from property.models import Property
from zone.models import Zone
from amenity.models import Amenity


class RoomieFunctionalityTests(APITestCase):
    """
    Tests para las nuevas funcionalidades de roomie matching.
    """

    def setUp(self):
        """Configuración inicial para los tests."""
        # Crear usuarios de prueba
        self.owner = User.objects.create_user(
            username='owner_test',
            email='owner@test.com',
            password='testpass123'
        )
        self.tenant = User.objects.create_user(
            username='tenant_test',
            email='tenant@test.com',
            password='testpass123'
        )
        self.roomie_seeker = User.objects.create_user(
            username='roomie_seeker_test',
            email='roomie@test.com',
            password='testpass123'
        )

        # Crear zona de prueba
        from django.contrib.gis.geos import Polygon
        # Crear un polígono simple para la zona (cuadrado pequeño alrededor del punto)
        polygon_coords = [
            (-68.101, -16.501),  # esquina inferior izquierda
            (-68.099, -16.501),  # esquina inferior derecha
            (-68.099, -16.499),  # esquina superior derecha
            (-68.101, -16.499),  # esquina superior izquierda
            (-68.101, -16.501),  # cerrar el polígono
        ]
        self.zone = Zone.objects.create(
            name="Zona Test",
            bounds=Polygon(polygon_coords)
        )

        # Crear SearchProfiles
        self.owner_profile = SearchProfile.objects.create(
            user=self.owner,
            location=Point(-68.1, -16.5),
            budget_min=500,
            budget_max=1000
        )
        self.owner_profile.preferred_zones.add(self.zone)

        self.tenant_profile = SearchProfile.objects.create(
            user=self.tenant,
            location=Point(-68.1, -16.5),
            budget_min=400,
            budget_max=800,
            roommate_preference='looking',
            roommate_preferences={'gender': 'any', 'smoker_ok': False},
            vibes=['deportista', 'estudiante']
        )
        self.tenant_profile.preferred_zones.add(self.zone)

        self.roomie_seeker_profile = SearchProfile.objects.create(
            user=self.roomie_seeker,
            location=Point(-68.1, -16.5),
            budget_min=300,
            budget_max=600,
            roommate_preference='looking',
            roommate_preferences={'gender': 'any', 'smoker_ok': True},
            vibes=['musico', 'artista']
        )
        self.roomie_seeker_profile.preferred_zones.add(self.zone)

        # Crear propiedad de prueba que permite roomies
        self.property_with_roomies = Property.objects.create(
            owner=self.owner,
            type='departamento',
            address='Av. Test 123',
            location=Point(-68.1, -16.5),
            zone=self.zone,
            price=700,
            description='Departamento amplio con 2 habitaciones',
            bedrooms=2,
            bathrooms=1,
            allows_roommates=True,
            max_occupancy=3,
            is_active=True
        )

        # Crear propiedad que NO permite roomies
        self.property_no_roomies = Property.objects.create(
            owner=self.owner,
            type='casa',
            address='Calle Test 456',
            location=Point(-68.1, -16.5),
            zone=self.zone,
            price=1200,
            description='Casa familiar',
            bedrooms=3,
            bathrooms=2,
            allows_roommates=False,
            is_active=True
        )

    def test_property_list_includes_roomie_seekers(self):
        """Test que el endpoint de propiedades incluya roomie seekers cuando se solicita."""
        self.client.force_authenticate(user=self.tenant)

        response = self.client.get('/api/properties/?include_roomies=true')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Manejar respuesta paginada
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
            
        self.assertIsInstance(results, list)

        # Verificar que hay tanto propiedades como roomie seekers
        roomie_seekers = [item for item in results if item.get('type') == 'roomie_seeker']
        properties = [item for item in results if item.get('type') != 'roomie_seeker']

        self.assertGreater(len(roomie_seekers), 0, "Debería haber roomie seekers en la respuesta")
        self.assertGreater(len(properties), 0, "Debería haber propiedades en la respuesta")

        # Verificar estructura de roomie seeker
        roomie = roomie_seekers[0]
        self.assertEqual(roomie['type'], 'roomie_seeker')
        self.assertTrue(roomie['is_roomie_listing'])
        self.assertIsNotNone(roomie['roomie_seeker_info'])
        self.assertIn('budget_min', roomie['roomie_seeker_info'])
        self.assertIn('roommate_preference', roomie['roomie_seeker_info'])

    def test_property_list_without_roomies(self):
        """Test que el endpoint de propiedades funcione normalmente sin roomie seekers."""
        self.client.force_authenticate(user=self.tenant)

        response = self.client.get('/api/properties/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que no hay roomie seekers cuando no se solicita
        if isinstance(response.data, list):
            roomie_seekers = [item for item in response.data if item.get('type') == 'roomie_seeker']
            self.assertEqual(len(roomie_seekers), 0, "No debería haber roomie seekers sin el parámetro")

    def test_convert_property_to_roomie_listing(self):
        """Test de conversión de propiedad a roomie listing."""
        self.client.force_authenticate(user=self.owner)

        data = {
            'tenant_profile_id': self.tenant_profile.id
        }

        response = self.client.post(
            f'/api/properties/{self.property_with_roomies.id}/convert-to-roomie/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que la propiedad fue actualizada
        self.property_with_roomies.refresh_from_db()
        self.assertTrue(self.property_with_roomies.is_roomie_listing)
        self.assertEqual(self.property_with_roomies.roomie_profile, self.tenant_profile)

    def test_convert_property_no_roomies_permission_denied(self):
        """Test que no se pueda convertir propiedad sin permisos."""
        self.client.force_authenticate(user=self.tenant)  # Tenant no es owner

        data = {
            'tenant_profile_id': self.tenant_profile.id
        }

        response = self.client.post(
            f'/api/properties/{self.property_with_roomies.id}/convert-to-roomie/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_convert_property_no_roomies_not_allowed(self):
        """Test que no se pueda convertir propiedad que no permite roomies."""
        self.client.force_authenticate(user=self.owner)

        data = {
            'tenant_profile_id': self.tenant_profile.id
        }

        response = self.client.post(
            f'/api/properties/{self.property_no_roomies.id}/convert-to-roomie/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Esta propiedad no permite roomies', response.data['error'])

    def test_available_roomies_endpoint(self):
        """Test del endpoint de roomies disponibles (sin propiedad asignada)."""
        self.client.force_authenticate(user=self.tenant)

        response = self.client.get('/api/roomie_search/available/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        # Verificar que solo incluye roomies sin propiedad asignada
        for roomie in response.data:
            self.assertEqual(roomie['type'], 'roomie_seeker')
            self.assertTrue(roomie['is_roomie_listing'])
            self.assertIn('roomie_seeker_info', roomie)

    def test_all_seekers_endpoint(self):
        """Test del endpoint de todos los roomie seekers."""
        self.client.force_authenticate(user=self.tenant)

        response = self.client.get('/api/roomie_search/all-seekers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        # Verificar que incluye todos los roomie seekers
        roomie_seekers_count = SearchProfile.objects.filter(
            roommate_preference__in=['looking', 'open']
        ).count()

        self.assertEqual(len(response.data), roomie_seekers_count)

        for roomie in response.data:
            self.assertEqual(roomie['type'], 'roomie_seeker')
            self.assertTrue(roomie['is_roomie_listing'])

    def test_roomie_seeker_serializer_structure(self):
        """Test de la estructura del RoomieSeekerPropertySerializer."""
        self.client.force_authenticate(user=self.tenant)

        response = self.client.get('/api/roomie_search/available/')

        if response.data:
            roomie = response.data[0]

            # Verificar campos requeridos
            required_fields = [
                'id', 'type', 'address', 'description', 'price', 'bedrooms',
                'bathrooms', 'size', 'zone_id', 'zone_name', 'latitude',
                'longitude', 'is_active', 'is_roomie_listing', 'roomie_seeker_info',
                'main_photo', 'nearby_properties_count', 'amenities',
                'created_at', 'updated_at'
            ]

            for field in required_fields:
                self.assertIn(field, roomie)

            # Verificar valores específicos
            self.assertEqual(roomie['type'], 'roomie_seeker')
            self.assertTrue(roomie['is_roomie_listing'])
            self.assertTrue(roomie['is_active'])

    def test_owner_accept_match_creates_roomie_listing(self):
        """Test que al aceptar un match se cree automáticamente roomie listing si aplica."""
        # Crear match entre tenant y propiedad
        match = Match.objects.create(
            match_type='property',
            subject_id=self.property_with_roomies.id,
            target_user=self.tenant,
            score=85.5,
            status='pending'
        )

        self.client.force_authenticate(user=self.owner)

        response = self.client.post(f'/api/matches/{match.id}/owner_accept/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que la propiedad se convirtió en roomie listing
        self.property_with_roomies.refresh_from_db()
        self.assertTrue(self.property_with_roomies.is_roomie_listing)
        self.assertEqual(self.property_with_roomies.roomie_profile, self.tenant_profile)

    def test_owner_accept_match_no_roomie_preference(self):
        """Test que no se cree roomie listing si el tenant no busca roomie."""
        # Cambiar preferencia del tenant
        self.tenant_profile.roommate_preference = 'no'
        self.tenant_profile.save()

        # Crear match
        match = Match.objects.create(
            match_type='property',
            subject_id=self.property_with_roomies.id,
            target_user=self.tenant,
            score=85.5,
            status='pending'
        )

        self.client.force_authenticate(user=self.owner)

        response = self.client.post(f'/api/matches/{match.id}/owner_accept/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que la propiedad NO se convirtió en roomie listing
        self.property_with_roomies.refresh_from_db()
        self.assertFalse(self.property_with_roomies.is_roomie_listing)
        self.assertIsNone(self.property_with_roomies.roomie_profile)

    def test_roomie_seeker_property_serializer_description(self):
        """Test del campo description en RoomieSeekerPropertySerializer."""
        self.client.force_authenticate(user=self.tenant)

        response = self.client.get('/api/roomie_search/available/')

        if response.data:
            roomie = response.data[0]
            description = roomie['description']

            # Verificar que el description contiene información relevante
            self.assertIn('Buscando roomie', description)
            self.assertIn('Presupuesto:', description)

            # Verificar que incluye vibes si existen
            if self.roomie_seeker_profile.vibes:
                self.assertIn('Intereses:', description)

            # Verificar que incluye preferencias de género si no es 'any'
            if self.roomie_seeker_profile.roommate_preferences.get('gender') != 'any':
                self.assertIn('Prefiere:', description)

    def test_roomie_seeker_property_serializer_address(self):
        """Test del campo address en RoomieSeekerPropertySerializer."""
        self.client.force_authenticate(user=self.tenant)

        response = self.client.get('/api/roomie_search/available/')

        if response.data:
            roomie = response.data[0]
            address = roomie['address']

            # Verificar que el address contiene información de zonas
            self.assertIn('Buscando en:', address)

            # Si hay zonas preferidas, deberían aparecer
            if self.roomie_seeker_profile.preferred_zones.exists():
                zone_names = [zone.name for zone in self.roomie_seeker_profile.preferred_zones.all()]
                for zone_name in zone_names:
                    self.assertIn(zone_name, address)

    def test_roomie_seeker_property_serializer_price(self):
        """Test del campo price en RoomieSeekerPropertySerializer."""
        self.client.force_authenticate(user=self.tenant)

        response = self.client.get('/api/roomie_search/available/')

        if response.data:
            roomie = response.data[0]
            price = roomie['price']

            # El price debería ser el budget_max o budget_min del perfil
            # Obtener el perfil del roomie seeker que fue convertido
            roomie_seekers = SearchProfile.objects.filter(
                roommate_preference__in=['looking', 'open']
            ).order_by('id')
            
            if roomie_seekers.exists():
                expected_profile = roomie_seekers.first()
                expected_price = expected_profile.budget_max or expected_profile.budget_min or 0
                self.assertEqual(float(price), float(expected_price))

    def test_authentication_required_for_roomie_endpoints(self):
        """Test que se requiere autenticación para endpoints de roomie."""
        # Sin autenticación
        response = self.client.get('/api/roomie_search/available/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get('/api/roomie_search/all-seekers/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RoomieSeekerPropertySerializerTest(TestCase):
    """
    Tests específicos para el RoomieSeekerPropertySerializer.
    """

    def setUp(self):
        """Configuración para tests del serializer."""
        self.user = User.objects.create_user(
            username='serializer_test',
            email='serializer@test.com',
            password='testpass123'
        )

        # Crear zona de prueba
        from django.contrib.gis.geos import Polygon
        # Crear un polígono simple para la zona (cuadrado pequeño alrededor del punto)
        polygon_coords = [
            (-68.101, -16.501),  # esquina inferior izquierda
            (-68.099, -16.501),  # esquina inferior derecha
            (-68.099, -16.499),  # esquina superior derecha
            (-68.101, -16.499),  # esquina superior izquierda
            (-68.101, -16.501),  # cerrar el polígono
        ]
        self.zone = Zone.objects.create(
            name="Zona Serializer Test",
            bounds=Polygon(polygon_coords)
        )

        self.profile = SearchProfile.objects.create(
            user=self.user,
            location=Point(-68.1, -16.5),
            budget_min=400,
            budget_max=700,
            roommate_preference='looking',
            roommate_preferences={'gender': 'female', 'smoker_ok': False},
            vibes=['estudiante', 'trabajador', 'ordenado']
        )
        self.profile.preferred_zones.add(self.zone)

    def test_serializer_basic_fields(self):
        """Test de campos básicos del serializer."""
        from property.serializers import RoomieSeekerPropertySerializer

        serializer = RoomieSeekerPropertySerializer(self.profile)
        data = serializer.data

        # Verificar campos calculados
        self.assertEqual(data['type'], 'roomie_seeker')
        self.assertTrue(data['is_roomie_listing'])
        self.assertTrue(data['is_active'])
        self.assertEqual(data['bedrooms'], 1)  # Valor por defecto
        self.assertEqual(data['bathrooms'], 1)  # Valor por defecto
        self.assertEqual(data['size'], 0)  # No aplicable

    def test_serializer_address_with_zones(self):
        """Test del campo address cuando hay zonas preferidas."""
        from property.serializers import RoomieSeekerPropertySerializer

        serializer = RoomieSeekerPropertySerializer(self.profile)
        data = serializer.data

        self.assertIn('Buscando en:', data['address'])
        self.assertIn(self.zone.name, data['address'])

    def test_serializer_address_without_zones(self):
        """Test del campo address cuando no hay zonas preferidas."""
        from property.serializers import RoomieSeekerPropertySerializer

        # Crear perfil sin zonas
        profile_no_zones = SearchProfile.objects.create(
            user=User.objects.create_user('no_zones_test'),
            location=Point(-68.1, -16.5),
            budget_min=300,
            budget_max=500,
            roommate_preference='looking'
        )

        serializer = RoomieSeekerPropertySerializer(profile_no_zones)
        data = serializer.data

        self.assertEqual(data['address'], "Zona no especificada")

    def test_serializer_description_with_all_fields(self):
        """Test del campo description con todos los campos disponibles."""
        from property.serializers import RoomieSeekerPropertySerializer

        serializer = RoomieSeekerPropertySerializer(self.profile)
        data = serializer.data
        description = data['description']

        # Verificar componentes del description
        self.assertIn('Buscando roomie', description)
        self.assertIn('Presupuesto:', description)
        self.assertIn('$400', description)  # budget_min
        self.assertIn('$700', description)  # budget_max
        self.assertIn('Intereses:', description)
        self.assertIn('estudiante', description)
        self.assertIn('Prefiere:', description)
        self.assertIn('female', description)  # gender preference

    def test_serializer_description_minimal_fields(self):
        """Test del campo description con campos mínimos."""
        from property.serializers import RoomieSeekerPropertySerializer

        # Crear perfil con campos mínimos
        profile_minimal = SearchProfile.objects.create(
            user=User.objects.create_user('minimal_test'),
            location=Point(-68.1, -16.5),
            budget_min=300,
            budget_max=500,
            roommate_preference='looking',
            roommate_preferences={'gender': 'any'},  # No smoker preference
            vibes=[]  # No vibes
        )

        serializer = RoomieSeekerPropertySerializer(profile_minimal)
        data = serializer.data
        description = data['description']

        # Verificar componentes básicos
        self.assertIn('Buscando roomie', description)
        self.assertIn('Presupuesto:', description)
        # No debería tener Intereses ni Prefiere (gender=any)
        self.assertNotIn('Intereses:', description)
        self.assertNotIn('Prefiere:', description)

    def test_serializer_zone_fields(self):
        """Test de los campos zone_id y zone_name."""
        from property.serializers import RoomieSeekerPropertySerializer

        serializer = RoomieSeekerPropertySerializer(self.profile)
        data = serializer.data

        self.assertEqual(data['zone_id'], self.zone.id)
        self.assertEqual(data['zone_name'], self.zone.name)

    def test_serializer_location_fields(self):
        """Test de los campos de ubicación."""
        from property.serializers import RoomieSeekerPropertySerializer

        serializer = RoomieSeekerPropertySerializer(self.profile)
        data = serializer.data

        self.assertEqual(data['latitude'], -16.5)
        self.assertEqual(data['longitude'], -68.1)

    def test_serializer_roomie_seeker_info(self):
        """Test del campo roomie_seeker_info."""
        from property.serializers import RoomieSeekerPropertySerializer
        from matching.serializers import SearchProfileSerializer

        serializer = RoomieSeekerPropertySerializer(self.profile)
        data = serializer.data
        roomie_info = data['roomie_seeker_info']

        # Verificar que es un SearchProfileSerializer válido
        self.assertIsInstance(roomie_info, dict)
        self.assertIn('user_id', roomie_info)
        self.assertIn('roommate_preference', roomie_info)
        self.assertIn('budget_min', roomie_info)
        self.assertIn('budget_max', roomie_info)
        self.assertIn('vibes', roomie_info)
        self.assertIn('roommate_preferences', roomie_info)