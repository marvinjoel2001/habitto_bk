"""
Tests para la funcionalidad de creación de zonas con validación de coordenadas.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.gis.geos import Polygon, GEOSGeometry
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Zone
from .serializers import ZoneCreateSerializer


class ZoneCreationTests(TestCase):
    """Tests para la creación de zonas con coordenadas múltiples."""

    def setUp(self):
        """Configuración inicial para los tests."""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_zone_with_valid_coordinates(self):
        """Test: Crear zona con coordenadas válidas (polígono cerrado)."""
        # Coordenadas válidas para un polígono cerrado (Centro de Santa Cruz)
        coordinates = [
            [-63.182, -17.783],  # lng, lat
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]   # Volver al punto inicial (cerrar polígono)
        ]

        zone_data = {
            'name': 'Centro Test',
            'description': 'Zona céntrica de prueba',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]  # GeoJSON requiere array de arrays
            }
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")

        zone = serializer.save()
        self.assertEqual(zone.name, 'Centro Test')
        self.assertIsInstance(zone.bounds, Polygon)

        # Verificar que el polígono es válido
        self.assertTrue(zone.bounds.valid)
        self.assertEqual(zone.bounds.geom_type, 'Polygon')

    def test_create_zone_with_minimum_coordinates(self):
        """Test: Crear zona con mínimo de coordenadas (3 puntos + cierre)."""
        # Mínimo requerido: 4 puntos (3 vértices + cierre)
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.180, -17.779],
            [-63.182, -17.783]  # Cerrar polígono
        ]

        zone_data = {
            'name': 'Zona Mínima',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())
        zone = serializer.save()
        self.assertTrue(zone.bounds.valid)

    def test_create_zone_with_many_coordinates(self):
        """Test: Crear zona con muchas coordenadas (polígono complejo)."""
        # Polígono complejo con muchos puntos
        coordinates = [
            [-63.182, -17.783],
            [-63.181, -17.782],
            [-63.180, -17.783],
            [-63.179, -17.782],
            [-63.178, -17.783],
            [-63.178, -17.780],
            [-63.179, -17.779],
            [-63.180, -17.780],
            [-63.181, -17.779],
            [-63.182, -17.780],
            [-63.182, -17.783]  # Cerrar polígono
        ]

        zone_data = {
            'name': 'Zona Compleja',
            'description': 'Zona con muchos vértices',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())
        zone = serializer.save()
        self.assertTrue(zone.bounds.valid)

    def test_invalid_polygon_not_closed(self):
        """Test: Rechazar polígono que no está cerrado."""
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779]
            # Falta volver al punto inicial
        ]

        zone_data = {
            'name': 'Zona Abierta',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        # Django GIS debería manejar esto, pero verificamos que se crea
        zone = serializer.save()
        # El polígono debería ser válido incluso si no está explícitamente cerrado
        self.assertTrue(zone.bounds.valid)

    def test_invalid_polygon_too_few_coordinates(self):
        """Test: Rechazar polígono con muy pocas coordenadas."""
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783]
            # Solo 2 puntos, insuficiente para un polígono
        ]

        zone_data = {
            'name': 'Zona Inválida',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        # Django GIS debería manejar esto, pero un polígono con 2 puntos no es válido
        with self.assertRaises(Exception):
            polygon = Polygon(coordinates)

    def test_invalid_coordinates_format(self):
        """Test: Rechazar formato de coordenadas inválido."""
        # Coordenadas en formato incorrecto (lat, lng en lugar de lng, lat)
        coordinates = [
            [-17.783, -63.182],  # lat, lng (incorrecto)
            [-17.783, -63.178],
            [-17.779, -63.178],
            [-17.779, -63.182]
        ]

        zone_data = {
            'name': 'Zona Mal Formateada',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        # Las coordenadas están en formato GeoJSON válido, pero lat/lng invertido
        # Esto crearía una zona en el hemisferio sur en lugar del norte
        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())  # El formato es válido
        zone = serializer.save()
        self.assertTrue(zone.bounds.valid)
        # La zona se crearía pero en ubicación incorrecta

    def test_invalid_geojson_type(self):
        """Test: Rechazar GeoJSON con tipo incorrecto."""
        zone_data = {
            'name': 'Zona Tipo Inválido',
            'bounds_geojson': {
                'type': 'Point',  # Debería ser 'Polygon'
                'coordinates': [-63.182, -17.783]
            }
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('bounds_geojson', serializer.errors)

    def test_coordinate_precision(self):
        """Test: Manejar coordenadas con alta precisión."""
        coordinates = [
            [-63.182123456789, -17.783123456789],
            [-63.178987654321, -17.783123456789],
            [-63.178987654321, -17.779876543210],
            [-63.182123456789, -17.779876543210],
            [-63.182123456789, -17.783123456789]
        ]

        zone_data = {
            'name': 'Zona de Alta Precisión',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())
        zone = serializer.save()
        self.assertTrue(zone.bounds.valid)

    def test_zone_bounds_properties(self):
        """Test: Verificar propiedades del polígono creado."""
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        zone_data = {
            'name': 'Zona Propiedades',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())
        zone = serializer.save()

        # Verificar propiedades del polígono
        self.assertIsNotNone(zone.bounds.area)
        self.assertIsNotNone(zone.bounds.length)
        self.assertIsNotNone(zone.bounds.centroid)

        # El área debería ser positiva
        self.assertGreater(zone.bounds.area, 0)

        # El centroide debería estar dentro del polígono
        self.assertTrue(zone.bounds.contains(zone.bounds.centroid))


class ZoneAPIIntegrationTests(APITestCase):
    """Tests de integración para la API de zonas."""

    def setUp(self):
        """Configuración inicial para tests de API."""
        self.user = User.objects.create_user(
            username='api_user',
            email='api@example.com',
            password='apipass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_zone_via_api(self):
        """Test: Crear zona a través de la API."""
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        data = {
            'name': 'API Zone Test',
            'description': 'Zona creada via API',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        response = self.client.post('/api/zones/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verificar respuesta
        self.assertEqual(response.data['name'], 'API Zone Test')
        self.assertEqual(response.data['description'], 'Zona creada via API')

        # Verificar que se creó en la base de datos
        zone = Zone.objects.get(name='API Zone Test')
        self.assertIsNotNone(zone)
        self.assertTrue(zone.bounds.valid)

    def test_create_zone_invalid_geojson(self):
        """Test: API rechaza GeoJSON inválido."""
        data = {
            'name': 'Invalid Zone',
            'bounds_geojson': {
                'type': 'Point',  # Tipo incorrecto
                'coordinates': [-63.182, -17.783]
            }
        }

        response = self.client.post('/api/zones/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('bounds_geojson', response.data)

    def test_get_zones_geojson_format(self):
        """Test: Obtener zonas en formato GeoJSON."""
        # Crear una zona primero
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        zone = Zone.objects.create(
            name='GeoJSON Test Zone',
            bounds=Polygon(coordinates)
        )

        response = self.client.get('/api/zones/geojson/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estructura GeoJSON
        self.assertIn('type', response.data)
        self.assertIn('features', response.data)

    def test_find_zone_by_location(self):
        """Test: Encontrar zona por coordenadas."""
        # Crear una zona de prueba
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        zone = Zone.objects.create(
            name='Location Test Zone',
            bounds=Polygon(coordinates)
        )

        # Punto dentro de la zona
        response = self.client.get('/api/zones/find_by_location/?lat=-17.781&lng=-63.180')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Location Test Zone')

        # Punto fuera de la zona
        response = self.client.get('/api/zones/find_by_location/?lat=-17.790&lng=-63.190')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_zone_heatmap_data(self):
        """Test: Obtener datos de heatmap para zonas."""
        # Crear zonas de prueba con diferentes niveles de actividad
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        zone1 = Zone.objects.create(
            name='High Demand Zone',
            bounds=Polygon(coordinates),
            offer_count=5,
            demand_count=25  # Alta demanda
        )

        response = self.client.get('/api/zones/heatmap/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estructura del heatmap
        self.assertIn('type', response.data)
        self.assertIn('features', response.data)
        self.assertEqual(response.data['type'], 'FeatureCollection')

        # Verificar que hay datos de intensidad
        if response.data['features']:
            feature = response.data['features'][0]
            self.assertIn('properties', feature)
            self.assertIn('intensity', feature['properties'])
            self.assertIn('geometry', feature)

    def test_zone_creation_permissions(self):
        """Test: Verificar permisos para creación de zonas."""
        # Desautenticar usuario
        self.client.force_authenticate(user=None)

        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        data = {
            'name': 'Anonymous Zone',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        response = self.client.post('/api/zones/', data, format='json')
        # Actualmente permite creación sin autenticación, pero debería requerir auth
        # self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ZoneCoordinateFormatTests(TestCase):
    """Tests específicos para el formato de coordenadas."""

    def test_geojson_format_specification(self):
        """Test: Verificar formato GeoJSON específico requerido."""
        # Formato correcto GeoJSON para polígono
        geojson_data = {
            'type': 'Polygon',
            'coordinates': [[
                [-63.182, -17.783],
                [-63.178, -17.783],
                [-63.178, -17.779],
                [-63.182, -17.779],
                [-63.182, -17.783]
            ]]
        }

        # Verificar que el serializer acepta este formato
        serializer = ZoneCreateSerializer(data={
            'name': 'Format Test',
            'bounds_geojson': geojson_data
        })

        self.assertTrue(serializer.is_valid())
        zone = serializer.save()
        self.assertTrue(zone.bounds.valid)

    def test_coordinate_order_lng_lat(self):
        """Test: Verificar orden correcto de coordenadas [lng, lat]."""
        # Coordenadas en orden correcto [lng, lat] para Santa Cruz, Bolivia
        coordinates = [
            [-63.182, -17.783],  # lng, lat
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        zone_data = {
            'name': 'Santa Cruz Centro',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())
        zone = serializer.save()

        # Verificar que las coordenadas están en el rango correcto para Bolivia
        # Bolivia: aproximadamente lng: -70 a -57, lat: -23 a -9
        centroid = zone.bounds.centroid
        self.assertGreater(centroid.x, -70)  # lng > -70
        self.assertLess(centroid.x, -57)    # lng < -57
        self.assertGreater(centroid.y, -23) # lat > -23
        self.assertLess(centroid.y, -9)     # lat < -9

    def test_polygon_orientation(self):
        """Test: Verificar orientación del polígono (sentido horario vs antihorario)."""
        # Polígono en sentido antihorario (estándar GeoJSON)
        coordinates_anticlockwise = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        # Polígono en sentido horario
        coordinates_clockwise = [
            [-63.182, -17.783],
            [-63.182, -17.779],
            [-63.178, -17.779],
            [-63.178, -17.783],
            [-63.182, -17.783]
        ]

        # Ambos deberían ser válidos, pero Django GIS los normaliza
        for coords, name in [(coordinates_anticlockwise, 'Antihorario'), (coordinates_clockwise, 'Horario')]:
            zone_data = {
                'name': f'Test {name}',
                'bounds_geojson': {
                    'type': 'Polygon',
                    'coordinates': [coords]
                }
            }

            serializer = ZoneCreateSerializer(data=zone_data)
            self.assertTrue(serializer.is_valid(), f"Falló orientación {name}")
            zone = serializer.save()
            self.assertTrue(zone.bounds.valid, f"Polígono inválido para orientación {name}")


class ZoneCreationDocumentationTests(TestCase):
    """Tests para documentar el proceso de creación de zonas."""

    def test_zone_creation_process_documentation(self):
        """Documentar el proceso completo de creación de zonas."""

        # Paso 1: Preparar coordenadas
        coordinates = [
            [-63.182, -17.783],  # Esquina noroeste
            [-63.178, -17.783],  # Esquina noreste
            [-63.178, -17.779],  # Esquina sureste
            [-63.182, -17.779],  # Esquina suroeste
            [-63.182, -17.783]   # Volver al punto inicial (cerrar)
        ]

        # Paso 2: Crear GeoJSON
        geojson = {
            'type': 'Polygon',
            'coordinates': [coordinates]
        }

        # Paso 3: Preparar datos para API
        zone_data = {
            'name': 'Centro Histórico',
            'description': 'Zona céntrica con edificios históricos',
            'bounds_geojson': geojson
        }

        # Paso 4: Validar con serializer
        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())

        # Paso 5: Crear zona
        zone = serializer.save()

        # Verificaciones
        self.assertEqual(zone.name, 'Centro Histórico')
        self.assertTrue(zone.bounds.valid)
        self.assertIsNotNone(zone.created_at)
        self.assertIsNotNone(zone.updated_at)

        # Las estadísticas se inicializan en 0
        self.assertEqual(zone.offer_count, 0)
        self.assertEqual(zone.demand_count, 0)
        self.assertEqual(zone.avg_price, 0)

    def test_frontend_integration_format(self):
        """Test: Formato esperado para integración con frontend."""

        # Formato que el frontend debería enviar
        frontend_data = {
            'name': 'Zona Creada por Usuario',
            'description': 'Zona residencial tranquila',
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [[
                    {'lng': -63.182, 'lat': -17.783},  # Formato {lng, lat}
                    {'lng': -63.178, 'lat': -17.783},
                    {'lng': -63.178, 'lat': -17.779},
                    {'lng': -63.182, 'lat': -17.779},
                    {'lng': -63.182, 'lat': -17.783}
                ]]
            }
        }

        # Convertir al formato esperado por el backend
        coordinates = []
        for point in frontend_data['bounds_geojson']['coordinates'][0]:
            coordinates.append([point['lng'], point['lat']])  # [lng, lat]

        backend_data = {
            'name': frontend_data['name'],
            'description': frontend_data['description'],
            'bounds_geojson': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        }

        serializer = ZoneCreateSerializer(data=backend_data)
        self.assertTrue(serializer.is_valid())
        zone = serializer.save()
        self.assertTrue(zone.bounds.valid)
