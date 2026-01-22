
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from .services.media_service import MediaService, CloudinaryProvider

class MediaServiceTest(TestCase):
    @patch('cloudinary.uploader.upload')
    def test_upload_image_success(self, mock_upload):
        # Mock response
        mock_upload.return_value = {
            'secure_url': 'https://res.cloudinary.com/demo/image/upload/v1/sample.jpg',
            'public_id': 'sample',
            'resource_type': 'image'
        }
        
        image = SimpleUploadedFile('test.jpg', b'test_content', content_type='image/jpeg')
        url = MediaService.upload_image(image)
        
        self.assertIn('https://', url)
        mock_upload.assert_called_once()
        args, kwargs = mock_upload.call_args
        self.assertEqual(kwargs['resource_type'], 'auto')

    @patch('cloudinary.uploader.upload')
    def test_upload_video_success(self, mock_upload):
        # Mock response
        mock_upload.return_value = {
            'secure_url': 'https://res.cloudinary.com/demo/video/upload/v1/sample.mp4',
            'public_id': 'sample_video',
            'resource_type': 'video'
        }
        
        video = SimpleUploadedFile('test.mp4', b'test_video_content', content_type='video/mp4')
        url = MediaService.upload_video(video)
        
        self.assertEqual(url, 'https://res.cloudinary.com/demo/video/upload/v1/sample.mp4')
        mock_upload.assert_called_once()
        args, kwargs = mock_upload.call_args
        self.assertEqual(kwargs['resource_type'], 'video')

    def test_upload_video_invalid_extension(self):
        video = SimpleUploadedFile('test.txt', b'test_content', content_type='text/plain')
        with self.assertRaises(Exception) as cm:
            MediaService.upload_video(video)
        self.assertIn('Formato de video no soportado', str(cm.exception))
