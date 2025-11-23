from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Property, PropertyOccupancy


class PropertyOccupancyAPITestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='o@example.com', password='pass')
        self.tenant = User.objects.create_user(username='tenant', email='t@example.com', password='pass')
        self.agent = User.objects.create_user(username='agent', email='a@example.com', password='pass')
        self.property = Property.objects.create(
            owner=self.owner,
            agent=self.agent,
            type='departamento',
            address='Calle 1',
            price='1000.00',
            guarantee='0.00',
            description='Desc',
            bedrooms=1,
            bathrooms=1,
            is_active=True,
        )

    def test_occupy_property(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('property-occupy', kwargs={'pk': self.property.pk})
        resp = self.client.post(url, {'tenant_id': self.tenant.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertFalse(self.property.is_available)
        occ = PropertyOccupancy.objects.filter(property=self.property, status='occupied').first()
        self.assertIsNotNone(occ)
        self.assertEqual(occ.tenant_id, self.tenant.id)

    def test_vacate_property(self):
        self.client.force_authenticate(user=self.owner)
        occupy_url = reverse('property-occupy', kwargs={'pk': self.property.pk})
        self.client.post(occupy_url, {'tenant_id': self.tenant.id}, format='json')
        vacate_url = reverse('property-vacate', kwargs={'pk': self.property.pk})
        resp = self.client.post(vacate_url, {
            'rating_tenant_by_owner': 5,
            'comment_tenant_by_owner': 'Ok'
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertTrue(self.property.is_available)
        occ = PropertyOccupancy.objects.filter(property=self.property).order_by('-start_date').first()
        self.assertEqual(occ.status, 'vacated')
        self.assertIsNotNone(occ.end_date)
        self.assertEqual(occ.rating_tenant_by_owner, 5)