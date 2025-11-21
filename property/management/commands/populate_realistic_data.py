#!/usr/bin/env python
"""
Script para poblar la base de datos con datos ficticios pero realistas.
Crea usuarios, propiedades, perfiles, zonas, amenidades y relaciones coherentes.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# Importar modelos
from matching.models import SearchProfile, Match
from property.models import Property, PropertyView, PropertyViewEvent
from zone.models import Zone, ZoneSearchLog
from amenity.models import Amenity
from paymentmethod.models import PaymentMethod
from user.models import UserProfile
from review.models import Review
from photo.models import Photo
from message.models import Message
from notification.models import Notification


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos ficticios pero realistas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Elimina los datos existentes antes de poblar',
        )

    def handle(self, *args, **options):
        if options['delete_existing']:
            self.stdout.write(self.style.WARNING('Eliminando datos existentes...'))
            self.delete_existing_data()

        self.stdout.write(self.style.SUCCESS('Iniciando población de datos...'))

        with transaction.atomic():
            self.create_zones()
            self.create_payment_methods()
            self.create_amenities()
            self.create_users_and_profiles()
            self.create_properties()
            self.create_reviews()
            self.create_property_views()
            self.create_messages()
            self.create_notifications()

        self.stdout.write(self.style.SUCCESS('¡Datos poblados exitosamente!'))

    def delete_existing_data(self):
        """Elimina datos existentes para empezar de cero."""
        models_to_delete = [
            Notification, Message, Review, PropertyViewEvent, PropertyView,
            Property, SearchProfile, UserProfile, User, ZoneSearchLog,
            Zone, Amenity, PaymentMethod
        ]

        for model in models_to_delete:
            try:
                model.objects.all().delete()
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error al eliminar {model.__name__}: {e}'))

    def create_zones(self):
        """Crea zonas de Santa Cruz realistas."""
        self.stdout.write('Creando zonas...')

        zones_data = [
            {
                'name': 'Centro',
                'description': 'Zona céntrica de Santa Cruz con acceso a comercios y servicios',
                'bounds': [(-17.783, -63.182), (-17.783, -63.178), (-17.779, -63.178), (-17.779, -63.182), (-17.783, -63.182)]
            },
            {
                'name': 'Equipetrol',
                'description': 'Zona residencial y comercial de alto nivel',
                'bounds': [(-17.774, -63.195), (-17.774, -63.185), (-17.764, -63.185), (-17.764, -63.195), (-17.774, -63.195)]
            },
            {
                'name': 'Urbarí',
                'description': 'Zona residencial tranquila con parques y áreas verdes',
                'bounds': [(-17.794, -63.205), (-17.794, -63.195), (-17.784, -63.195), (-17.784, -63.205), (-17.794, -63.205)]
            },
            {
                'name': 'Cotoca',
                'description': 'Zona tradicional con mercado artesanal',
                'bounds': [(-17.814, -63.225), (-17.814, -63.215), (-17.804, -63.215), (-17.804, -63.225), (-17.814, -63.225)]
            },
            {
                'name': 'Palmas',
                'description': 'Zona moderna con centros comerciales y restaurantes',
                'bounds': [(-17.764, -63.215), (-17.764, -63.205), (-17.754, -63.205), (-17.754, -63.215), (-17.764, -63.215)]
            }
        ]

        from django.contrib.gis.geos import Polygon
        self.zones = []
        for zone_data in zones_data:
            zone = Zone.objects.create(
                name=zone_data['name'],
                bounds=Polygon(zone_data['bounds']),
                description=zone_data['description']
            )
            self.zones.append(zone)

    def create_payment_methods(self):
        """Crea métodos de pago comunes."""
        self.stdout.write('Creando métodos de pago...')

        payment_methods = [
            'Efectivo', 'Transferencia bancaria', 'Tarjeta de crédito',
            'Tarjeta de débito', 'Depósito bancario', 'Cheque',
            'Pago móvil (QR)', 'PayPal', 'Western Union'
        ]

        self.payment_methods = []
        for method in payment_methods:
            pm = PaymentMethod.objects.create(name=method)
            self.payment_methods.append(pm)

    def create_amenities(self):
        """Crea amenidades comunes."""
        self.stdout.write('Creando amenidades...')

        amenities_data = [
            'Wi-Fi',
            'Aire acondicionado',
            'Piscina',
            'Gimnasio',
            'Parqueo',
            'Seguridad 24h',
            'Lavadora',
            'Cocina equipada',
            'Terraza',
            'Jardín',
            'Calefacción',
            'TV por cable',
            'Mascotas permitidas',
            'Fumadores permitidos',
            'Acceso discapacitados'
        ]

        self.amenities = []
        for amenity_name in amenities_data:
            amenity = Amenity.objects.create(
                name=amenity_name
            )
            self.amenities.append(amenity)

    def create_users_and_profiles(self):
        """Crea usuarios con perfiles realistas."""
        self.stdout.write('Creando usuarios y perfiles...')

        # Datos realistas de usuarios
        users_data = [
            # Propietarios
            {'username': 'carlos_mendoza', 'email': 'carlos.m@email.com', 'first_name': 'Carlos', 'last_name': 'Mendoza', 'type': 'owner'},
            {'username': 'maria_rodriguez', 'email': 'maria.r@email.com', 'first_name': 'María', 'last_name': 'Rodríguez', 'type': 'owner'},
            {'username': 'juan_perez', 'email': 'juan.p@email.com', 'first_name': 'Juan', 'last_name': 'Pérez', 'type': 'owner'},
            {'username': 'ana_gomez', 'email': 'ana.g@email.com', 'first_name': 'Ana', 'last_name': 'Gómez', 'type': 'owner'},

            # Inquilinos que buscan roomie
            {'username': 'laura_silva', 'email': 'laura.s@email.com', 'first_name': 'Laura', 'last_name': 'Silva', 'type': 'tenant_roomie'},
            {'username': 'pedro_ramirez', 'email': 'pedro.r@email.com', 'first_name': 'Pedro', 'last_name': 'Ramírez', 'type': 'tenant_roomie'},
            {'username': 'sofia_torres', 'email': 'sofia.t@email.com', 'first_name': 'Sofía', 'last_name': 'Torres', 'type': 'tenant_roomie'},
            {'username': 'diego_morales', 'email': 'diego.m@email.com', 'first_name': 'Diego', 'last_name': 'Morales', 'type': 'tenant_roomie'},

            # Inquilinos normales
            {'username': 'andrea_flores', 'email': 'andrea.f@email.com', 'first_name': 'Andrea', 'last_name': 'Flores', 'type': 'tenant'},
            {'username': 'miguel_castro', 'email': 'miguel.c@email.com', 'first_name': 'Miguel', 'last_name': 'Castro', 'type': 'tenant'},
            {'username': 'valentina_rios', 'email': 'valentina.r@email.com', 'first_name': 'Valentina', 'last_name': 'Ríos', 'type': 'tenant'},
            {'username': 'alejandro_suarez', 'email': 'alejandro.s@email.com', 'first_name': 'Alejandro', 'last_name': 'Suárez', 'type': 'tenant'},

            # Agentes inmobiliarios
            {'username': 'roberto_vargas', 'email': 'roberto.v@email.com', 'first_name': 'Roberto', 'last_name': 'Vargas', 'type': 'agent'},
            {'username': 'claudia_mendez', 'email': 'claudia.m@email.com', 'first_name': 'Claudia', 'last_name': 'Méndez', 'type': 'agent'},
        ]

        # Vibras/intereses comunes
        vibes_list = [
            ['estudiante', 'tranquilo', 'ordenado'],
            ['trabajador', 'deportista', 'social'],
            ['musico', 'artista', 'creativo'],
            ['programador', 'gamer', 'nocturno'],
            ['chef', 'gourmet', 'social'],
            ['lector', 'estudioso', 'tranquilo'],
            ['emprendedor', 'ambicioso', 'activo'],
            ['viajero', 'aventurero', 'social']
        ]

        self.users = []
        self.profiles = []

        for user_data in users_data:
            # Crear usuario
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password='sistemas123',
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )

            # Crear perfil de usuario
            profile = UserProfile.objects.create(
                user=user,
                phone=f'7{random.randint(1000000, 9999999)}',
                user_type='propietario' if user_data['type'] == 'owner' else 'agente' if user_data['type'] == 'agent' else 'inquilino',
                is_verified=random.choice([True, False, False])  # 33% verificados
            )

            # Crear SearchProfile según el tipo
            if user_data['type'] in ['tenant', 'tenant_roomie']:
                # Coordenadas dentro de Santa Cruz
                lat = -17.78 + random.uniform(-0.02, 0.02)
                lon = -63.18 + random.uniform(-0.02, 0.02)

                search_profile = SearchProfile.objects.create(
                    user=user,
                    location=Point(lon, lat),
                    budget_min=random.randint(300, 800),
                    budget_max=random.randint(800, 1500),
                    bedrooms_min=random.randint(1, 3),
                    bedrooms_max=random.randint(1, 3),
                    age=random.randint(18, 35),
                    gender=random.choice(['male', 'female']),
                    children_count=random.randint(0, 2) if random.choice([True, False]) else 0,
                    smoker=random.choice([True, False]),
                    pets_count=random.randint(0, 2) if random.choice([True, False]) else 0,
                    stable_job=random.choice([True, False]),
                    roommate_preference='looking' if user_data['type'] == 'tenant_roomie' else random.choice(['no', 'open']),
                    roommate_preferences={
                        'gender': random.choice(['any', 'male', 'female']),
                        'smoker_ok': random.choice([True, False]),
                        'pets_ok': random.choice([True, False]),
                        'age_min': random.randint(18, 25),
                        'age_max': random.randint(25, 40)
                    },
                    vibes=random.choice(vibes_list),
                    occupation=random.choice(['Estudiante', 'Profesional', 'Empresario', 'Freelancer', 'Comerciante'])
                )

                # Asignar zonas preferidas
                preferred_zones = random.sample(self.zones, random.randint(1, 3))
                search_profile.preferred_zones.set(preferred_zones)
                self.profiles.append(search_profile)

            self.users.append(user)

    def create_properties(self):
        """Crea propiedades realistas."""
        self.stdout.write('Creando propiedades...')

        # Direcciones realistas de Santa Cruz
        addresses = [
            'Av. San Martín #123', 'Calle 21 de Mayo #456', 'Av. Cristo Redentor #789',
            'Calle Warnes #321', 'Av. Grigotá #654', 'Calle Urubó #987',
            'Av. Busch #147', 'Calle Rene Moreno #258', 'Av. Beni #369',
            'Calle Junín #741', 'Av. Pirai #852', 'Calle Aroma #963',
            'Av. 2 de Agosto #159', 'Calle Monseñor Salvatierra #357',
            'Av. Banzer #486', 'Calle La Paz #279', 'Av. Velasco #183'
        ]

        # Descripciones de propiedades
        descriptions = [
            'Hermoso departamento con excelente ubicación, cerca de centros comerciales y universidades.',
            'Casa amplia con jardín, ideal para familias. Zona segura y tranquila.',
            'Habitación en departamento compartido, ambiente joven y responsable.',
            'Departamento moderno con todas las comodidades, excelente vista.',
            'Casa familiar con espacios amplios, cerca de colegios y parques.',
            'Habitación cómoda en zona céntrica, transporte público cercano.',
            'Departamento amoblado, listo para habitar. Ideal para estudiantes.',
            'Casa con piscina y áreas verdes, perfecta para disfrutar el clima.',
            'Habitación económica en zona segura, ambiente tranquilo.',
            'Departamento de lujo con amenities completos, zona exclusiva.'
        ]

        # Propietarios disponibles
        owners = [u for u in self.users if u.username in ['carlos_mendoza', 'maria_rodriguez', 'juan_perez', 'ana_gomez']]

        self.properties = []

        for i in range(15):
            owner = random.choice(owners)
            zone = random.choice(self.zones)

            # Coordenadas dentro de la zona
            lat = -17.78 + random.uniform(-0.02, 0.02)
            lon = -63.18 + random.uniform(-0.02, 0.02)

            # Tipo de propiedad
            prop_type = random.choice(['casa', 'departamento', 'habitacion', 'anticretico'])

            # Precios según tipo
            if prop_type == 'habitacion':
                price = random.randint(300, 600)
                bedrooms = 1
                bathrooms = 1
                size = random.randint(15, 25)
            elif prop_type == 'departamento':
                price = random.randint(600, 1200)
                bedrooms = random.randint(1, 3)
                bathrooms = random.randint(1, 2)
                size = random.randint(40, 120)
            else:  # casa o anticretico
                price = random.randint(800, 2000)
                bedrooms = random.randint(2, 4)
                bathrooms = random.randint(1, 3)
                size = random.randint(80, 200)

            # Crear propiedad
            property_obj = Property.objects.create(
                owner=owner,
                type=prop_type,
                address=random.choice(addresses),
                location=Point(lon, lat),
                zone=zone,
                price=price,
                guarantee=price * random.uniform(0.5, 1.0),
                description=random.choice(descriptions),
                size=size,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                availability_date=timezone.now() + timedelta(days=random.randint(0, 30)),
                is_active=random.choice([True, True, True, False]),  # 75% activas
                allows_roommates=random.choice([True, False]),
                max_occupancy=random.randint(2, 5) if prop_type != 'habitacion' else 2,
                min_price_per_person=price // random.randint(2, 3) if prop_type != 'habitacion' else None,
                is_furnished=random.choice([True, False]),
                preferred_tenant_gender=random.choice(['any', 'male', 'female']),
                children_allowed=random.choice([True, False]),
                pets_allowed=random.choice([True, False]),
                smokers_allowed=random.choice([True, False]),
                students_only=random.choice([True, False]),
                stable_job_required=random.choice([True, False])
            )

            # Asignar amenidades aleatorias
            property_amenities = random.sample(self.amenities, random.randint(2, 8))
            property_obj.amenities.set(property_amenities)

            # Asignar métodos de pago
            payment_methods = random.sample(self.payment_methods, random.randint(2, 4))
            property_obj.accepted_payment_methods.set(payment_methods)

            # Algunas propiedades pueden ser roomie listings
            if property_obj.allows_roommates and random.choice([True, False]):
                # Buscar un perfil de roomie seeker para asignar
                roomie_profiles = [p for p in self.profiles if p.roommate_preference == 'looking']
                if roomie_profiles:
                    property_obj.is_roomie_listing = True
                    property_obj.roomie_profile = random.choice(roomie_profiles)
                    property_obj.save()

            self.properties.append(property_obj)

    def create_reviews(self):
        """Crea reseñas realistas."""
        self.stdout.write('Creando reseñas...')

        review_texts = [
            'Excelente lugar, muy bien ubicado y el propietario muy atento.',
            'El departamento es cómodo pero necesita algunas reparaciones.',
            'Muy buena experiencia, zona segura y tranquila.',
            'El precio es justo por lo que ofrece, recomendado.',
            'Tuve algunos problemas con los vecinos pero el lugar es bueno.',
            'Perfecto para estudiantes, cerca de todo y económico.',
            'Las fotos no le hacen justicia, es mucho mejor en persona.',
            'El propietario responde rápido y soluciona los problemas.',
            'Muy buenas instalaciones, todo funciona correctamente.',
            'Zona excelente, cerca de transporte y comercios.'
        ]

        # Crear reseñas para algunas propiedades
        for property_obj in random.sample(self.properties, min(8, len(self.properties))):
            # 1-3 reseñas por propiedad
            num_reviews = random.randint(1, 3)
            for _ in range(num_reviews):
                reviewer = random.choice([u for u in self.users if u != property_obj.owner])
                Review.objects.create(
                    property=property_obj,
                    user=reviewer,
                    rating=random.randint(3, 5),
                    comment=random.choice(review_texts)
                )

    def create_property_views(self):
        """Crea vistas de propiedades."""
        self.stdout.write('Creando vistas de propiedades...')

        for property_obj in random.sample(self.properties, min(10, len(self.properties))):
            # 2-5 usuarios ven cada propiedad
            viewers = random.sample(self.users, random.randint(2, 5))
            for viewer in viewers:
                if viewer != property_obj.owner:
                    # Crear eventos de vista
                    for _ in range(random.randint(1, 3)):
                        PropertyViewEvent.objects.create(
                            user=viewer,
                            property=property_obj
                        )

                    # Crear contador de vistas
                    PropertyView.objects.create(
                        user=viewer,
                        property=property_obj,
                        count=random.randint(1, 5)
                    )

    def create_messages(self):
        """Crea mensajes entre usuarios."""
        self.stdout.write('Creando mensajes...')

        message_contents = [
            'Hola, me interesa tu propiedad. ¿Podemos hablar?',
            '¿Está disponible para visitar este fin de semana?',
            'Tengo algunas preguntas sobre las amenidades.',
            '¿El precio es negociable?',
            'Me gustaría programar una visita.',
            '¿Se aceptan mascotas pequeñas?',
            '¿Cuáles son los requisitos para rentar?',
            'Estoy interesado, ¿podemos coordinar?',
            '¿Incluye los servicios públicos en el precio?',
            '¿Hay algún contrato mínimo?'
        ]

        # Crear conversaciones entre usuarios aleatorios
        for _ in range(min(10, len(self.users))):
            sender = random.choice(self.users)
            receiver = random.choice([u for u in self.users if u != sender])
            
            # Crear 1-3 mensajes por conversación
            for _ in range(random.randint(1, 3)):
                Message.objects.create(
                    sender=sender,
                    receiver=receiver,
                    content=random.choice(message_contents),
                    is_read=random.choice([True, False])
                )

    def create_notifications(self):
        """Crea notificaciones."""
        self.stdout.write('Creando notificaciones...')

        notification_types = [
            'new_match', 'new_message', 'property_viewed', 'review_received',
            'property_approved', 'payment_reminder', 'match_accepted'
        ]

        messages = {
            'new_match': 'Tienes un nuevo match con una propiedad',
            'new_message': 'Tienes un mensaje nuevo',
            'property_viewed': 'Alguien vio tu propiedad',
            'review_received': 'Recibiste una nueva reseña',
            'property_approved': 'Tu propiedad fue aprobada',
            'payment_reminder': 'Recuerda realizar tu pago',
            'match_accepted': 'Tu match fue aceptado'
        }

        # Crear notificaciones para algunos usuarios
        for user in random.sample(self.users, min(8, len(self.users))):
            # 1-4 notificaciones por usuario
            for _ in range(random.randint(1, 4)):
                notif_type = random.choice(notification_types)
                Notification.objects.create(
                    user=user,
                    message=messages[notif_type] + ' hace ' + str(random.randint(1, 24)) + ' horas',
                    is_read=random.choice([True, False])
                )


# Para ejecutar como comando de Django
if __name__ == '__main__':
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bk_habitto.settings')
    import django
    django.setup()

    # Ejecutar el comando
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
