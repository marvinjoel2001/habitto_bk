from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient
from property.models import Property
from zone.models import Zone

class PropertyUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a Zone
        self.zone = Zone.objects.create(
            name='Test Zone',
            bounds='POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))'
        )
        
        # Create Parent Property (Building)
        self.parent = Property.objects.create(
            owner=self.user,
            type='casa', # Assuming 'edificio' isn't in choices yet, but 'casa' works
            address='Av Banzer',
            price=100000,
            location=Point(5, 5),
            description='Edificio Principal'
        )

    def test_unit_creation_and_inheritance(self):
        # Create Unit without location
        unit = Property.objects.create(
            owner=self.user,
            type='departamento',
            address='Av Banzer 101',
            price=500,
            parent_property=self.parent,
            unit_number='101',
            description='Depto 101'
        )
        
        # Reload from DB
        unit.refresh_from_db()
        
        # Check inheritance
        self.assertEqual(unit.location, self.parent.location)
        self.assertEqual(unit.zone, self.zone) # Should detect zone from inherited location
        self.assertEqual(unit.parent_property, self.parent)
        self.assertEqual(unit.unit_number, '101')

    def test_serializer_units(self):
        # Create a unit
        unit = Property.objects.create(
            owner=self.user,
            type='departamento',
            address='Av Banzer 102',
            price=500,
            parent_property=self.parent,
            unit_number='102',
            description='Depto 102'
        )
        
        # Test Parent Serializer
        from property.serializers import PropertySerializer
        serializer = PropertySerializer(self.parent)
        data = serializer.data
        
        self.assertTrue('units' in data)
        self.assertEqual(len(data['units']), 1)
        self.assertEqual(data['units'][0]['id'], unit.id)
        self.assertEqual(data['units'][0]['unit_number'], '102')

    def test_smart_zones_with_units(self):
        # Create 10 units
        for i in range(10):
            Property.objects.create(
                owner=self.user,
                type='departamento',
                address=f'Av Banzer 10{i}',
                price=500,
                parent_property=self.parent,
                description=f'Depto 10{i}',
                is_active=True,
                is_available=True
            )
            
        # Parent is active too
        self.parent.is_active = True
        self.parent.is_available = True
        self.parent.save()
        
        # Call Hexagon Service
        from zone.services import HexagonGridService
        geojson = HexagonGridService.get_hex_grid_with_stats()
        
        # Check if we have features
        features = geojson['features']
        self.assertTrue(len(features) > 0)
        
        # The count should be 11 (1 Parent + 10 Units)
        # OR 10 if parent is filtered?
        # Current logic counts everything active.
        props = features[0]['properties']
        # Depending on grid alignment, they might be in same hex.
        # Since they have EXACT same location, they must be in same hex.
        self.assertEqual(props['count'], 11)
