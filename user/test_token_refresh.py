from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import timedelta
import time

class TokenRefreshTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.verify_url = reverse('token_verify')

    def test_token_lifecycle(self):
        # 1. Login to get tokens
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']
        refresh_token = response.data['refresh']

        # 2. Verify access token
        response = self.client.post(self.verify_url, {'token': access_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Refresh token
        response = self.client.post(self.refresh_url, {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_access_token = response.data['access']
        new_refresh_token = response.data['refresh']

        self.assertNotEqual(access_token, new_access_token)
        # Since rotation is enabled, refresh token should also change
        self.assertNotEqual(refresh_token, new_refresh_token)

        # 4. Verify new access token
        response = self.client.post(self.verify_url, {'token': new_access_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Try to use old refresh token (should fail due to blacklist)
        response = self.client.post(self.refresh_url, {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_refresh_token(self):
        response = self.client.post(self.refresh_url, {'refresh': 'invalid_token'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
