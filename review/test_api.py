from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import Review
from property.models import Property


class ReviewAPITestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='ownerpass123'
        )
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='reviewerpass123'
        )
        
        self.property = Property.objects.create(
            owner=self.owner,
            type='casa',
            address='Calle Test 123',
            price=Decimal('1500.00'),
            description='Casa de prueba',
            bedrooms=3,
            bathrooms=2
        )
        
        self.review = Review.objects.create(
            property=self.property,
            user=self.reviewer,
            rating=5,
            comment='Excelente propiedad'
        )
        
    def test_create_review(self):
        """Test crear reseña"""
        self.client.force_authenticate(user=self.reviewer)
        url = reverse('review-list')
        data = {
            'property': self.property.id,
            'user': self.reviewer.id,
            'rating': 4,
            'comment': 'Muy buena propiedad'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 2)
        
    def test_list_reviews(self):
        """Test listar reseñas"""
        self.client.force_authenticate(user=self.reviewer)
        url = reverse('review-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
    def test_retrieve_review(self):
        """Test obtener reseña específica"""
        self.client.force_authenticate(user=self.reviewer)
        url = reverse('review-detail', kwargs={'pk': self.review.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 5)
        
    def test_update_review(self):
        """Test actualizar reseña"""
        self.client.force_authenticate(user=self.reviewer)
        url = reverse('review-detail', kwargs={'pk': self.review.pk})
        data = {'rating': 4}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 4)
        
    def test_delete_review(self):
        """Test eliminar reseña"""
        self.client.force_authenticate(user=self.reviewer)
        url = reverse('review-detail', kwargs={'pk': self.review.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Review.objects.count(), 0)