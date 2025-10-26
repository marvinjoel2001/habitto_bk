# Generated migration for initial zone data

from django.db import migrations
from django.contrib.gis.geos import Polygon


def create_initial_zones(apps, schema_editor):
    """
    Crea 10 zonas iniciales para Santa Cruz de la Sierra, Bolivia
    con coordenadas reales y polígonos aproximados de cada zona.
    """
    Zone = apps.get_model('zone', 'Zone')
    
    # Datos de zonas reales de Santa Cruz de la Sierra
    zones_data = [
        {
            'name': 'Centro',
            'description': 'Zona céntrica de Santa Cruz, área comercial y financiera principal',
            'avg_price': 2500.00,
            'offer_count': 0,
            'demand_count': 0,
            # Polígono aproximado del centro de Santa Cruz
            'bounds': Polygon((
                (-63.1825, -17.7833),  # Esquina suroeste
                (-63.1825, -17.7733),  # Esquina noroeste
                (-63.1725, -17.7733),  # Esquina noreste
                (-63.1725, -17.7833),  # Esquina sureste
                (-63.1825, -17.7833)   # Cerrar polígono
            ))
        },
        {
            'name': 'Plan 3000',
            'description': 'Zona residencial popular al norte de la ciudad',
            'avg_price': 800.00,
            'offer_count': 0,
            'demand_count': 0,
            'bounds': Polygon((
                (-63.1200, -17.7200),
                (-63.1200, -17.7000),
                (-63.1000, -17.7000),
                (-63.1000, -17.7200),
                (-63.1200, -17.7200)
            ))
        },
        {
            'name': 'Equipetrol',
            'description': 'Zona residencial de alto nivel, moderna y exclusiva',
            'avg_price': 4500.00,
            'offer_count': 0,
            'demand_count': 0,
            'bounds': Polygon((
                (-63.1500, -17.7600),
                (-63.1500, -17.7500),
                (-63.1400, -17.7500),
                (-63.1400, -17.7600),
                (-63.1500, -17.7600)
            ))
        },
        {
            'name': 'Las Palmas',
            'description': 'Zona residencial consolidada con buena infraestructura',
            'avg_price': 2200.00,
            'offer_count': 0,
            'demand_count': 0,
            'bounds': Polygon((
                (-63.1600, -17.7700),
                (-63.1600, -17.7600),
                (-63.1500, -17.7600),
                (-63.1500, -17.7700),
                (-63.1600, -17.7700)
            ))
        },
        {
            'name': 'Villa 1ro de Mayo',
            'description': 'Zona residencial tradicional al oeste de la ciudad',
            'avg_price': 1500.00,
            'offer_count': 0,
            'demand_count': 0,
            'bounds': Polygon((
                (-63.2000, -17.7800),
                (-63.2000, -17.7700),
                (-63.1900, -17.7700),
                (-63.1900, -17.7800),
                (-63.2000, -17.7800)
            ))
        },
        {
            'name': 'Barrio Hamacas',
            'description': 'Zona residencial al sur, en crecimiento',
            'avg_price': 1200.00,
            'offer_count': 0,
            'demand_count': 0,
            'bounds': Polygon((
                (-63.1700, -17.8000),
                (-63.1700, -17.7900),
                (-63.1600, -17.7900),
                (-63.1600, -17.8000),
                (-63.1700, -17.8000)
            ))
        },
        {
            'name': 'Zona Norte',
            'description': 'Área de expansión urbana al norte de la ciudad',
            'avg_price': 1800.00,
            'offer_count': 0,
            'demand_count': 0,
            'bounds': Polygon((
                (-63.1400, -17.7400),
                (-63.1400, -17.7300),
                (-63.1300, -17.7300),
                (-63.1300, -17.7400),
                (-63.1400, -17.7400)
            ))
        },
        {
            'name': 'Zona Este',
            'description': 'Zona en desarrollo con nuevos proyectos residenciales',
            'avg_price': 2000.00,
            'offer_count': 0,
            'demand_count': 0,
            'bounds': Polygon((
                (-63.1300, -17.7800),
                (-63.1300, -17.7700),
                (-63.1200, -17.7700),
                (-63.1200, -17.7800),
                (-63.1300, -17.7800)
            ))
        },
        {
            'name': 'Zona Sur',
            'description': 'Área residencial al sur con buena conectividad',
            'avg_price': 1600.00,
            'offer_count': 0,
            'demand_count': 0,
            'bounds': Polygon((
                (-63.1800, -17.8100),
                (-63.1800, -17.8000),
                (-63.1700, -17.8000),
                (-63.1700, -17.8100),
                (-63.1800, -17.8100)
            ))
        },
        {
            'name': 'Zona Oeste',
            'description': 'Área residencial tradicional con servicios consolidados',
            'avg_price': 1400.00,
            'offer_count': 0,
            'demand_count': 0,
            'bounds': Polygon((
                (-63.2100, -17.7900),
                (-63.2100, -17.7800),
                (-63.2000, -17.7800),
                (-63.2000, -17.7900),
                (-63.2100, -17.7900)
            ))
        }
    ]
    
    # Crear las zonas
    for zone_data in zones_data:
        Zone.objects.create(**zone_data)


def reverse_initial_zones(apps, schema_editor):
    """Elimina las zonas iniciales"""
    Zone = apps.get_model('zone', 'Zone')
    Zone.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('zone', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_zones, reverse_initial_zones),
    ]