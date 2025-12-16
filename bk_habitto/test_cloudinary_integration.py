
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

class ImageUploadTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        self.upload_url = reverse('image-upload')

    @patch('bk_habitto.services.cloudinary_service.cloudinary_url')
    @patch('bk_habitto.services.cloudinary_service.cloudinary.uploader.upload')
    def test_upload_image_success(self, mock_upload, mock_cloudinary_url):
        # Mock response from Cloudinary
        mock_upload.return_value = {
            'secure_url': 'https://res.cloudinary.com/demo/image/upload/v1/sample.jpg',
            'public_id': 'sample'
        }
        # Mock cloudinary_url to return a tuple (url, options)
        mock_cloudinary_url.return_value = ('https://res.cloudinary.com/demo/image/upload/f_auto,q_auto/v1/sample.jpg', {})

        image = SimpleUploadedFile('test.jpg', b'test_content', content_type='image/jpeg')
        data = {'file': image}

        response = self.client.post(self.upload_url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('url', response.data)
        # Check that it returns optimized url
        self.assertEqual(response.data['url'], 'https://res.cloudinary.com/demo/image/upload/f_auto,q_auto/v1/sample.jpg')

class PropertyCloudinaryTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='password')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('property-list')

    def test_create_property_with_photos_urls(self):
        data = {
            'type': 'casa',
            'address': 'Test Address',
            'price': 1000,
            'description': 'A beautiful house',
            'latitude': -17.0,
            'longitude': -63.0,
            'photos_urls': [
                'https://res.cloudinary.com/demo/image/upload/v1/photo1.jpg',
                'https://res.cloudinary.com/demo/image/upload/v1/photo2.jpg'
            ]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify JSONField
        self.assertEqual(len(response.data['photos_urls']), 2)

        # Verify Photo objects creation
        from property.models import Property
        prop = Property.objects.get(id=response.data['id'])
        self.assertEqual(prop.photos.count(), 2)
        self.assertEqual(prop.photos.first().image_url, data['photos_urls'][0])

class UserProfileCloudinaryTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

    def test_update_profile_picture_url(self):
        url = reverse('userprofile-update-me')
        data = {
            'profile_picture_url': 'https://res.cloudinary.com/demo/image/upload/v1/profile.jpg'
        }

        # First ensure profile exists
        from user.models import UserProfile
        UserProfile.objects.get_or_create(user=self.user)

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify URL stored
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.profile_picture_url, data['profile_picture_url'])

        # Verify history
        self.assertEqual(self.user.profile.picture_history.count(), 1)
        self.assertEqual(self.user.profile.picture_history.first().image_url, data['profile_picture_url'])
