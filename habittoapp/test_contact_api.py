from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch

class ContactApiTests(APITestCase):
    def test_contact_email_async(self):
        """
        Test that the contact endpoint returns immediately and calls the async task.
        """
        url = reverse('contact-message')
        data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'This is a test message.'
        }
        
        # Patch the Celery task to verify it's called
        with patch('habittoapp.tasks.send_contact_email_task.delay') as mock_task:
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'sent')
            
            # Verify the task was called with the correct data
            mock_task.assert_called_once()
            args, _ = mock_task.call_args
            task_data = args[0]
            self.assertEqual(task_data['email'], 'test@example.com')
            self.assertEqual(task_data['message'], 'This is a test message.')
