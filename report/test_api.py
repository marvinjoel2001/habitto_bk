from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.gis.geos import Point
from decimal import Decimal

from report.models import Report, ReportCategory
from property.models import Property
from notification.models import Notification


class ReportAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reporter', email='rep@example.com', password='x')
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='x')
        self.client.force_authenticate(user=self.user)
        self.category = ReportCategory.objects.create(name='Información falsa', scope='property')
        self.prop = Property.objects.create(owner=self.owner, type='casa', address='Rep 123', location=Point(-63.1821, -17.7834), price=Decimal('1200.00'), description='Desc', bedrooms=2, bathrooms=1)

    def test_create_property_report(self):
        url = reverse('report-list')
        payload = {
            'target_type': 'property',
            'target_property': self.prop.id,
            'category': self.category.id,
            'title': 'Dirección incorrecta',
            'description': 'La dirección no coincide con la realidad.'
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Report.objects.filter(reporter=self.user, target_property=self.prop).exists())
        # Notificación de recepción
        self.assertTrue(Notification.objects.filter(user=self.user, message__icontains='fue recibido').exists())

    def test_list_my_reports(self):
        Report.objects.create(reporter=self.user, target_type='property', target_property=self.prop, category=self.category, title='T', description='Descripción suficiente')
        resp = self.client.get(reverse('report-my'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data
        items = data.get('results') if isinstance(data, dict) else data
        self.assertTrue(items)

    def test_admin_update_status(self):
        report = Report.objects.create(reporter=self.user, target_type='property', target_property=self.prop, category=self.category, title='T', description='Descripción suficiente')
        admin = User.objects.create_superuser(username='admin', email='a@example.com', password='x')
        self.client.force_authenticate(user=admin)
        url = reverse('report-update-status', kwargs={'pk': report.id})
        resp = self.client.post(url, {'status': 'in_review'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        report.refresh_from_db()
        self.assertEqual(report.status, 'in_review')
        self.assertTrue(Notification.objects.filter(user=self.user, message__icontains='cambió a estado').exists())

