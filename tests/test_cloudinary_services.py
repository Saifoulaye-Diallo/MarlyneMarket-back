"""
Unit tests for Cloudinary utilities and helpers.
"""
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO

from apps.catalog.services import CloudinaryImageService


class CloudinaryImageServiceTestCase(TestCase):
    """Test Cloudinary image service utilities."""
    
    def create_test_image(self, width=100, height=100, format='JPEG'):
        """Create a test image file."""
        image = Image.new('RGB', (width, height), color='blue')
        image_io = BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)
        
        extension = 'jpg' if format == 'JPEG' else format.lower()
        return SimpleUploadedFile(
            f'test.{extension}',
            image_io.getvalue(),
            content_type=f'image/{extension}'
        )
    
    def test_validate_image_file_valid(self):
        """Test validation of valid image files."""
        valid_image = self.create_test_image()
        
        # Should not raise any exception
        try:
            CloudinaryImageService.validate_image_file(valid_image)
        except Exception as e:
            self.fail(f"Valid image raised exception: {e}")
    
    def test_validate_image_file_invalid_type(self):
        """Test validation rejection of invalid file types."""
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'This is not an image',
            content_type='text/plain'
        )
        
        with self.assertRaises(ValueError) as context:
            CloudinaryImageService.validate_image_file(invalid_file)
        
        self.assertIn('Invalid file type', str(context.exception))
    
    def test_validate_image_file_too_large(self):
        """Test validation rejection of files that are too large."""
        # Create a file that's too large (mock the size)
        large_image = self.create_test_image()
        large_image.size = 6 * 1024 * 1024  # 6MB
        
        with self.assertRaises(ValueError) as context:
            CloudinaryImageService.validate_image_file(large_image)
        
        self.assertIn('File size too large', str(context.exception))
    
    @patch('cloudinary.uploader.upload')
    def test_upload_image_success(self, mock_upload):
        """Test successful image upload."""
        mock_upload.return_value = {
            'public_id': 'test_123',
            'secure_url': 'https://res.cloudinary.com/test/image/upload/test_123.jpg',
            'format': 'jpg',
            'bytes': 1024
        }
        
        image = self.create_test_image()
        result = CloudinaryImageService.upload_image(image, 'product_123')
        
        self.assertEqual(result['public_id'], 'test_123')
        self.assertIn('secure_url', result)
        mock_upload.assert_called_once()
    
    @patch('cloudinary.uploader.upload')
    def test_upload_image_with_error(self, mock_upload):
        """Test image upload with Cloudinary error."""
        mock_upload.side_effect = Exception('Cloudinary error')
        
        image = self.create_test_image()
        
        with self.assertRaises(Exception):
            CloudinaryImageService.upload_image(image, 'product_123')
    
    @patch('cloudinary.uploader.destroy')
    def test_delete_image_success(self, mock_destroy):
        """Test successful image deletion."""
        mock_destroy.return_value = {'result': 'ok'}
        
        result = CloudinaryImageService.delete_image('test_public_id')
        
        self.assertEqual(result['result'], 'ok')
        mock_destroy.assert_called_once_with('test_public_id')
    
    @patch('cloudinary.uploader.destroy')
    def test_delete_image_not_found(self, mock_destroy):
        """Test deletion of non-existent image."""
        mock_destroy.return_value = {'result': 'not found'}
        
        result = CloudinaryImageService.delete_image('nonexistent_id')
        
        self.assertEqual(result['result'], 'not found')
    
    def test_generate_upload_options(self):
        """Test generation of upload options."""
        options = CloudinaryImageService.generate_upload_options('product_123')
        
        self.assertIn('folder', options)
        self.assertIn('use_filename', options)
        self.assertIn('unique_filename', options)
        self.assertIn('overwrite', options)
        self.assertEqual(options['folder'], 'marketplace/products')
    
    def test_extract_public_id_from_url(self):
        """Test extraction of public_id from Cloudinary URL."""
        url = 'https://res.cloudinary.com/test/image/upload/v1234567890/marketplace/products/test_123.jpg'
        public_id = CloudinaryImageService.extract_public_id_from_url(url)
        
        self.assertEqual(public_id, 'marketplace/products/test_123')
    
    def test_extract_public_id_from_invalid_url(self):
        """Test extraction from invalid URL."""
        invalid_url = 'https://example.com/image.jpg'
        public_id = CloudinaryImageService.extract_public_id_from_url(invalid_url)
        
        self.assertIsNone(public_id)


class CloudinaryIntegrationTestCase(TestCase):
    """Integration tests for full Cloudinary workflow."""
    
    @patch('cloudinary.uploader.upload')
    @patch('cloudinary.uploader.destroy')
    def test_full_upload_and_delete_workflow(self, mock_destroy, mock_upload):
        """Test complete upload and delete workflow."""
        # Mock responses
        mock_upload.return_value = {
            'public_id': 'marketplace/products/test_123',
            'secure_url': 'https://res.cloudinary.com/test/image/upload/marketplace/products/test_123.jpg',
            'format': 'jpg',
            'bytes': 1024
        }
        mock_destroy.return_value = {'result': 'ok'}
        
        # Create test image
        image = SimpleUploadedFile(
            'test.jpg',
            b'fake_image_content',
            content_type='image/jpeg'
        )
        
        # Upload
        upload_result = CloudinaryImageService.upload_image(image, 'product_123')
        self.assertIn('secure_url', upload_result)
        
        # Extract public_id and delete
        public_id = CloudinaryImageService.extract_public_id_from_url(upload_result['secure_url'])
        delete_result = CloudinaryImageService.delete_image(public_id)
        
        self.assertEqual(delete_result['result'], 'ok')
        
        # Verify calls
        mock_upload.assert_called_once()
        mock_destroy.assert_called_once_with(public_id)