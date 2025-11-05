from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.gis.geos import Point
from decimal import Decimal
from property.models import Property
from notification.models import Notification
from message.models import Message
from matching.models import SearchProfile, Match
from matching.models import MatchFeedback


class MatchingAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tenant', email='tenant@example.com', password='tenantpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_search_profile(self):
        url = reverse('search-profile-list')
        data = {
            'latitude': -17.7834,
            'longitude': -63.1821,
            'budget_min': '400.00',
            'budget_max': '800.00',
            'desired_types': ['departamento']
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        sp = SearchProfile.objects.get(user=self.user)
        self.assertIsNotNone(sp.location)

    def test_property_creation_triggers_match(self):
        # Crear SearchProfile primero (cercano y con presupuesto)
        sp_url = reverse('search-profile-list')
        self.client.post(sp_url, {
            'latitude': -17.7834,
            'longitude': -63.1821,
            'budget_min': '400.00',
            'budget_max': '800.00',
            'desired_types': ['departamento']
        }, format='json')

        # Crear propiedad que debe matchear alto
        p_url = reverse('property-list')
        response = self.client.post(p_url, {
            'type': 'departamento',
            'address': 'Avenida Nueva 456',
            'latitude': -17.7834,
            'longitude': -63.1821,
            'price': '600.00',
            'description': 'Departamento moderno',
            'bedrooms': 1,
            'bathrooms': 1,
            'allows_roommates': False
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Obtener propiedad creada por address
        created_prop = Property.objects.get(address='Avenida Nueva 456')
        # Verificar que se haya creado un Match para el usuario
        matches = Match.objects.filter(match_type='property', subject_id=created_prop.id, target_user=self.user)
        self.assertTrue(matches.exists())

    def test_list_matches_and_accept(self):
        # Generar contexto: perfil y propiedad con match
        sp = SearchProfile.objects.create(user=self.user, location=Point(-63.1821, -17.7834), budget_min=Decimal('400.00'), budget_max=Decimal('800.00'))
        owner_user = User.objects.create_user(username='owner', email='owner@example.com', password='ownerpass123')
        prop = Property.objects.create(owner=owner_user, type='departamento', address='X', location=Point(-63.1821, -17.7834), price=Decimal('600.00'), description='Y', bedrooms=1, bathrooms=1)
        Match.objects.create(match_type='property', subject_id=prop.id, target_user=self.user, score=85.0, metadata={})

        # Listar matches desde el perfil de búsqueda
        response = self.client.get(f'/api/search_profiles/{sp.id}/matches/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

        # Aceptar primer match
        data = response.data
        items = data.get('results') if isinstance(data, dict) else data
        self.assertTrue(items)
        match_id = items[0]['id']
        accept_resp = self.client.post(f'/api/matches/{match_id}/accept/')
        self.assertEqual(accept_resp.status_code, status.HTTP_200_OK)
        m = Match.objects.get(id=match_id)
        self.assertEqual(m.status, 'accepted')
        # Debe crear notificación para el inquilino y mensaje al propietario
        self.assertTrue(Notification.objects.filter(user=self.user, message__icontains='Match aceptado').exists())
        self.assertTrue(Message.objects.filter(sender=self.user, receiver=owner_user).exists())
        # Notificar también al propietario que hay interés
        self.assertTrue(Notification.objects.filter(user=owner_user, message__icontains='interesado en tu propiedad').exists())

    def test_recommendations_mixed(self):
        # Crear perfil del usuario y datos que generen recomendaciones
        sp = SearchProfile.objects.create(
            user=self.user,
            location=Point(-63.1821, -17.7834),
            budget_min=Decimal('400.00'),
            budget_max=Decimal('800.00'),
            desired_types=['departamento']
        )
        # Propiedad cercana y dentro de presupuesto
        Property.objects.create(
            owner=self.user,
            type='departamento',
            address='Rec X',
            location=Point(-63.1821, -17.7834),
            price=Decimal('600.00'),
            description='Rec Prop',
            bedrooms=1,
            bathrooms=1,
            is_active=True
        )
        # Otro perfil para roommate con presupuestos compatibles
        other_user = User.objects.create_user(username='other', email='other@example.com', password='otherpass123')
        SearchProfile.objects.create(
            user=other_user,
            location=Point(-63.1821, -17.7834),
            budget_min=Decimal('450.00'),
            budget_max=Decimal('750.00'),
            desired_types=['departamento']
        )

        # Obtener recomendaciones mixtas
        resp = self.client.get('/api/recommendations/?type=mixed')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        results = resp.data['results']
        # Debe incluir al menos recomendaciones de propiedades
        has_property = any(item.get('type') == 'property' for item in results)
        self.assertTrue(has_property)

    def test_match_feedback_create(self):
        # Crear match de prueba
        prop = Property.objects.create(
            owner=self.user,
            type='departamento',
            address='FBK',
            location=Point(-63.1821, -17.7834),
            price=Decimal('600.00'),
            description='FBK Prop',
            bedrooms=1,
            bathrooms=1,
            is_active=True
        )
        match = Match.objects.create(match_type='property', subject_id=prop.id, target_user=self.user, score=85.0, metadata={})
        payload = {
            'match': match.id,
            'user': self.user.id,
            'feedback_type': 'like',
            'reason': 'Buen precio y ubicación'
        }
        resp = self.client.post('/api/match_feedback/', payload, format='json')
        self.assertIn(resp.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        self.assertTrue(MatchFeedback.objects.filter(match=match, user=self.user, feedback_type='like').exists())

    def test_recommendations_property_type(self):
        # Perfil del usuario
        SearchProfile.objects.create(
            user=self.user,
            location=Point(-63.1821, -17.7834),
            budget_min=Decimal('400.00'),
            budget_max=Decimal('800.00'),
            desired_types=['departamento']
        )
        # Propiedad activa y cercana
        owner_user = User.objects.create_user(username='prop_owner', email='prop_owner@example.com', password='ownerpass123')
        Property.objects.create(
            owner=owner_user,
            type='departamento',
            address='Rec Prop Only',
            location=Point(-63.1821, -17.7834),
            price=Decimal('650.00'),
            description='Prop para recomendaciones type=property',
            bedrooms=1,
            bathrooms=1,
            is_active=True
        )

        # Solicitar recomendaciones solo de propiedades
        resp = self.client.get('/api/recommendations/?type=property')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        results = resp.data['results']
        self.assertTrue(results, msg='Debe retornar al menos una recomendación de propiedad')
        # Verificar que todas sean del tipo property y con match correspondiente
        for item in results:
            self.assertEqual(item.get('type'), 'property')
            match = item.get('match')
            self.assertIsInstance(match, dict)
            self.assertEqual(match.get('match_type'), 'property')

    def test_recommendations_roommate_type(self):
        # Perfil del usuario
        SearchProfile.objects.create(
            user=self.user,
            location=Point(-63.1821, -17.7834),
            budget_min=Decimal('400.00'),
            budget_max=Decimal('800.00'),
            desired_types=['departamento']
        )
        # Otro usuario con perfil compatible para generar match de roomie
        other_user = User.objects.create_user(username='roomie_other', email='roomie_other@example.com', password='roomiepass123')
        SearchProfile.objects.create(
            user=other_user,
            location=Point(-63.1821, -17.7834),
            budget_min=Decimal('450.00'),
            budget_max=Decimal('750.00'),
            desired_types=['departamento']
        )

        # Solicitar recomendaciones solo de roomies
        resp = self.client.get('/api/recommendations/?type=roommate')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        results = resp.data['results']
        self.assertTrue(results, msg='Debe retornar al menos una recomendación de roomie')
        # Verificar que todas sean del tipo roommate y con match correspondiente
        for item in results:
            self.assertEqual(item.get('type'), 'roommate')
            match = item.get('match')
            self.assertIsInstance(match, dict)
            self.assertEqual(match.get('match_type'), 'roommate')