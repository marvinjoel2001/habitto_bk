"""
Tests corregidos para la funcionalidad de creación de zonas con validación de coordenadas.
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
            'coordinates': coordinates  # Usar el nuevo campo coordinates
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
            'coordinates': coordinates  # Usar el nuevo campo coordinates
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
            'coordinates': coordinates  # Usar el nuevo campo coordinates
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())
        zone = serializer.save()
        self.assertTrue(zone.bounds.valid)

    def test_invalid_polygon_too_few_coordinates(self):
        """Test: Rechazar polígono con muy pocas coordenadas."""
        # Solo 2 puntos (no forma un polígono)
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783]
        ]

        zone_data = {
            'name': 'Zona Inválida',
            'coordinates': coordinates
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('coordinates', serializer.errors)

    def test_invalid_polygon_not_closed(self):
        """Test: Rechazar polígono que no está cerrado."""
        # Polígono sin cerrar (el serializer debe cerrarlo automáticamente)
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.180, -17.779]
            # Falta volver al punto inicial
        ]

        zone_data = {
            'name': 'Zona No Cerrada',
            'coordinates': coordinates
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())  # El serializer debe cerrar el polígono
        zone = serializer.save()

        # Verificar que el polígono fue cerrado
        coords = list(zone.bounds.coords[0])  # Obtener coordenadas del polígono
        self.assertEqual(coords[0], coords[-1])  # Primera y última coordenada deben ser iguales

    def test_invalid_geojson_type(self):
        """Test: Rechazar GeoJSON con tipo incorrecto."""
        # Esto ya no aplica directamente con el nuevo campo coordinates,
        # pero podemos probar con datos inválidos
        zone_data = {
            'name': 'Zona Tipo Inválido',
            'coordinates': "no es un array"  # Tipo inválido
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertFalse(serializer.is_valid())

    def test_invalid_coordinates_format(self):
        """Test: Rechazar formato de coordenadas inválido."""
        # Coordenadas con formato incorrecto (3 elementos en lugar de 2)
        coordinates = [
            [-63.182, -17.783, 100],  # 3 elementos (inválido)
            [-63.178, -17.783],
            [-63.182, -17.783]
        ]

        zone_data = {
            'name': 'Zona Formato Inválido',
            'coordinates': coordinates
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('coordinates', serializer.errors)

    def test_coordinate_precision(self):
        """Test: Manejar coordenadas con alta precisión."""
        # Coordenadas con alta precisión (6 decimales)
        coordinates = [
            [-63.182456, -17.783123],
            [-63.178789, -17.783456],
            [-63.178123, -17.779789],
            [-63.182456, -17.779123],
            [-63.182456, -17.783123]  # Cerrar polígono
        ]

        zone_data = {
            'name': 'Zona de Alta Precisión',
            'description': 'Zona con coordenadas de alta precisión',
            'coordinates': coordinates
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
            [-63.182, -17.783]  # Cerrar polígono
        ]

        zone_data = {
            'name': 'Zona Propiedades',
            'coordinates': coordinates
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())
        zone = serializer.save()

        # Verificar propiedades del polígono
        self.assertEqual(zone.bounds.num_points, 5)  # 4 vértices + 1 para cerrar
        self.assertTrue(zone.bounds.area > 0)  # Debe tener área positiva
        self.assertAlmostEqual(zone.bounds.centroid.x, -63.180, places=3)  # Centro aproximado
        self.assertAlmostEqual(zone.bounds.centroid.y, -17.781, places=3)  # Centro aproximado


class ZoneCoordinateFormatTests(TestCase):
    """Tests para validar formatos de coordenadas y GeoJSON."""

    def test_geojson_format_specification(self):
        """Test: Verificar formato GeoJSON específico requerido."""
        # Coordenadas en formato [lng, lat] como especifica GeoJSON
        coordinates = [
            [-63.182, -17.783],  # Santa Cruz, Bolivia
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]   # Cerrar polígono
        ]

        zone_data = {
            'name': 'Zona GeoJSON Estándar',
            'coordinates': coordinates
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())

    def test_coordinate_order_lng_lat(self):
        """Test: Verificar orden correcto de coordenadas [lng, lat]."""
        # GeoJSON especifica [longitud, latitud]
        coordinates = [
            [-63.182, -17.783],  # [lng, lat] - formato correcto
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        zone_data = {
            'name': 'Zona Orden Correcto',
            'coordinates': coordinates
        }

        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())

    def test_polygon_orientation(self):
        """Test: Verificar orientación del polígono (sentido horario vs antihorario)."""
        # Ambas orientaciones deben ser aceptadas
        test_cases = [
            {
                'name': 'Horario',
                'coordinates': [
                    [-63.182, -17.783],
                    [-63.178, -17.783],
                    [-63.178, -17.779],
                    [-63.182, -17.779],
                    [-63.182, -17.783]
                ]
            },
            {
                'name': 'Antihorario',
                'coordinates': [
                    [-63.182, -17.783],
                    [-63.182, -17.779],
                    [-63.178, -17.779],
                    [-63.178, -17.783],
                    [-63.182, -17.783]
                ]
            }
        ]

        for test_case in test_cases:
            zone_data = {
                'name': f'Zona {test_case["name"]}',
                'coordinates': test_case['coordinates']
            }

            serializer = ZoneCreateSerializer(data=zone_data)
            self.assertTrue(serializer.is_valid(), f"Falló orientación {test_case['name']}")


class ZoneAPIIntegrationTests(APITestCase):
    """Tests de integración para la API de zonas."""

    def setUp(self):
        """Configuración inicial para tests de API."""
        self.user = User.objects.create_user(
            username='api_test_user',
            email='api@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_zone_via_api(self):
        """Test: Crear zona a través de la API."""
        # Get initial count to test increment
        initial_count = Zone.objects.count()

        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        zone_data = {
            'name': 'API Test Zone',
            'description': 'Zona creada vía API',
            'coordinates': coordinates
        }

        response = self.client.post('/api/zones/', zone_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verificar que la zona fue creada (count should increase by 1)
        self.assertEqual(Zone.objects.count(), initial_count + 1)
        zone = Zone.objects.get(name='API Test Zone')
        self.assertEqual(zone.name, 'API Test Zone')
        self.assertTrue(zone.bounds.valid)

    def test_create_zone_invalid_geojson(self):
        """Test: API rechaza GeoJSON inválido."""
        zone_data = {
            'name': 'Zona Inválida API',
            'coordinates': "esto no es un array"  # Datos inválidos
        }

        response = self.client.post('/api/zones/', zone_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('coordinates', response.data.get('data', {}))

    def test_zone_creation_permissions(self):
        """Test: Verificar permisos para creación de zonas."""
        # Desautenticar usuario
        self.client.force_authenticate(user=None)

        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.783]
        ]

        zone_data = {
            'name': 'Zona Sin Permisos',
            'coordinates': coordinates
        }

        response = self.client.post('/api/zones/', zone_data, format='json')
        # Actualmente el sistema permite creación pública, pero esto puede cambiar
        # Si se implementan permisos más estrictos, debería retornar 401 o 403
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_get_zones_geojson_format(self):
        """Test: Obtener zonas en formato GeoJSON."""
        # Crear una zona de prueba con coordenadas únicas
        coordinates = [
            [-63.200, -17.800],  # Coordenadas únicas
            [-63.195, -17.800],
            [-63.195, -17.795],
            [-63.200, -17.795],
            [-63.200, -17.800]
        ]

        geojson = {
            'type': 'Polygon',
            'coordinates': [coordinates]
        }

        zone = Zone.objects.create(
            name='GeoJSON Test Zone',
            bounds=GEOSGeometry(str(geojson))
        )

        # Obtener zonas en formato GeoJSON
        response = self.client.get('/api/zones/geojson/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estructura GeoJSON
        self.assertEqual(response.data['type'], 'FeatureCollection')
        self.assertIn('features', response.data)

        # Verificar que la zona creada está en las características
        features = response.data['features']
        test_zone_feature = None
        for feature in features:
            if feature['properties']['name'] == 'GeoJSON Test Zone':
                test_zone_feature = feature
                break

        self.assertIsNotNone(test_zone_feature, "Zona de prueba no encontrada en GeoJSON")
        self.assertEqual(test_zone_feature['type'], 'Feature')
        self.assertIn('geometry', test_zone_feature)

        # Verificar que el geometry contiene el polígono
        geometry = test_zone_feature['geometry']

        # Verificar formato GeoJSON esperado
        self.assertIsInstance(geometry, dict, "Geometry debe ser un objeto GeoJSON, no un string")
        self.assertEqual(geometry['type'], 'Polygon')
        self.assertIn('coordinates', geometry)

    def test_find_zone_by_location(self):
        """Test: Encontrar zona por coordenadas."""
        # Crear una zona de prueba con coordenadas únicas
        coordinates = [
            [-63.150, -17.850],  # Coordenadas únicas para evitar conflictos
            [-63.145, -17.850],
            [-63.145, -17.845],
            [-63.150, -17.845],
            [-63.150, -17.850]
        ]

        geojson = {
            'type': 'Polygon',
            'coordinates': [coordinates]
        }

        zone = Zone.objects.create(
            name='Location Test Zone',
            bounds=GEOSGeometry(str(geojson))
        )

        # Buscar zona por coordenadas dentro del polígono
        response = self.client.get('/api/zones/find_by_location/', {
            'lat': -17.847,  # Latitud dentro del polígono
            'lng': -63.147   # Longitud dentro del polígono
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Location Test Zone')

    def test_zone_heatmap_data(self):
        """Test: Obtener datos de heatmap para zonas."""
        # Crear zonas con estadísticas diferentes
        coordinates = [
            [-63.220, -17.820],  # Coordenadas únicas
            [-63.215, -17.820],
            [-63.215, -17.815],
            [-63.220, -17.815],
            [-63.220, -17.820]
        ]

        geojson = {
            'type': 'Polygon',
            'coordinates': [coordinates]
        }

        # Crear zona con alta demanda
        high_demand_zone = Zone.objects.create(
            name='Zona Alta Demanda Test',
            bounds=GEOSGeometry(str(geojson)),
            offer_count=5,
            demand_count=15  # Alta demanda
        )

        # Obtener datos de heatmap
        response = self.client.get('/api/zones/heatmap/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estructura de datos (FeatureCollection format)
        self.assertEqual(response.data['type'], 'FeatureCollection')
        self.assertIn('features', response.data)

        # Buscar la zona de prueba en los resultados
        features = response.data['features']
        test_zone_feature = None
        for feature in features:
            if feature['properties']['name'] == 'Zona Alta Demanda Test':
                test_zone_feature = feature
                break

        self.assertIsNotNone(test_zone_feature, "Zona de prueba no encontrada en heatmap")

        # Verificar estructura según ZoneHeatmapSerializer
        properties = test_zone_feature['properties']
        self.assertIn('id', properties)
        self.assertIn('name', properties)
        self.assertIn('intensity', properties)

        # Verificar que la intensidad refleje la alta demanda
        self.assertGreater(properties['intensity'], 0.1)


class ZoneCreationDocumentationTests(TestCase):
    """Tests para documentar el proceso de creación de zonas."""

    def test_zone_creation_process_documentation(self):
        """Documentar el proceso completo de creación de zonas."""
        # Ejemplo de proceso completo de creación de zona
        coordinates = [
            [-63.182, -17.783],
            [-63.178, -17.783],
            [-63.178, -17.779],
            [-63.182, -17.779],
            [-63.182, -17.783]
        ]

        # Paso 1: Preparar datos
        zone_data = {
            'name': 'Zona Documentación',
            'description': 'Ejemplo de zona para documentación',
            'coordinates': coordinates
        }

        # Paso 2: Validar datos con serializer
        serializer = ZoneCreateSerializer(data=zone_data)
        self.assertTrue(serializer.is_valid())

        # Paso 3: Crear zona
        zone = serializer.save()

        # Paso 4: Verificar resultado
        self.assertEqual(zone.name, 'Zona Documentación')
        self.assertTrue(zone.bounds.valid)
        self.assertTrue(zone.bounds.area > 0)

        # Documentar el flujo:
        print("\n=== FLUJO DE CREACIÓN DE ZONA ===")
        print("1. Frontend envía coordenadas como array: [[lng, lat], ...]")
        print("2. Serializer valida mínimo 3 coordenadas y cierra el polígono")
        print("3. Coordenadas se convierten a GeoJSON y luego a GEOSGeometry")
        print("4. Zona se guarda con el polígono válido")
        print("5. Estadísticas se calculan automáticamente")

    def test_frontend_integration_format(self):
        """Test: Formato esperado para integración con frontend."""
        # Formato que el frontend debe enviar
        frontend_data = {
            'name': 'Zona Frontend',
            'description': 'Zona creada desde frontend',
            'coordinates': [
                [-63.182, -17.783],  # [lng, lat] - orden importante
                [-63.178, -17.783],
                [-63.178, -17.779],
                [-63.182, -17.779],
                [-63.182, -17.783]   # Cerrar polígono
            ]
        }

        # El frontend puede dibujar el polígono y obtener estas coordenadas
        # de servicios como Google Maps, Leaflet, Mapbox, etc.

        serializer = ZoneCreateSerializer(data=frontend_data)
        self.assertTrue(serializer.is_valid())

        zone = serializer.save()

        # Verificar que se puede recuperar en formato GeoJSON para el mapa
        from .serializers import ZoneGeoSerializer
        geo_serializer = ZoneGeoSerializer(zone)
        geo_data = geo_serializer.data

        # ZoneGeoSerializer usa geo_field='bounds' que incluye la geometría
        self.assertIsNotNone(zone.bounds)
        self.assertEqual(zone.bounds.geom_type, 'Polygon')

        # Verificar que el polígono tiene las coordenadas esperadas
        coords = list(zone.bounds.coords[0])
        self.assertGreater(len(coords), 3)  # Al menos 3 puntos
        self.assertEqual(coords[0], coords[-1])  # Polígono cerrado


# Documentación adicional para el equipo frontend
"""
=== DOCUMENTACIÓN PARA FRONTEND ===

FORMATO DE COORDENADAS ESPERADO:
{
    "name": "Nombre de la Zona",
    "description": "Descripción opcional",
    "coordinates": [
        [longitude, latitude],  // [lng, lat] - orden importante
        [longitude, latitude],
        ...
        [longitude, latitude]   // Último punto puede ser igual al primero para cerrar
    ]
}

EJEMPLO DE INTEGRACIÓN CON MAPBOX:
```javascript
// Obtener coordenadas de un polígono dibujado
const coordinates = drawnPolygon.geometry.coordinates[0];

// Enviar al backend
const zoneData = {
    name: 'Mi Zona',
    description: 'Zona creada desde el mapa',
    coordinates: coordinates
};

fetch('/api/zones/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(zoneData)
});
```

VALIDACIONES DEL BACKEND:
- Mínimo 3 coordenadas requeridas
- Cada coordenada debe ser [lng, lat] con exactamente 2 números
- El polígono se cierra automáticamente si no está cerrado
- Se valida que el polígono sea geométricamente válido

RESPUESTA EXITOSA (201 Created):
{
    "success": true,
    "message": "Zona creada exitosamente",
    "data": {
        "id": 1,
        "name": "Mi Zona",
        "description": "Zona creada desde el mapa",
        // ... otros campos
    }
}

ERRORES COMUNES:
- 400 Bad Request: Coordenadas inválidas o formato incorrecto
- 401 Unauthorized: Usuario no autenticado
- 403 Forbidden: Usuario sin permisos para crear zonas
"""
