"""
Tests for Cloudinary image upload integration.
"""
import tempfile
import os
from PIL import Image
from io import BytesIO
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import SellerProfile
from apps.catalog.models import Category, ProductType, Product, ProductImage

User = get_user_model()


class CloudinaryImageUploadTestCase(APITestCase):
    """Test Cloudinary image upload functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user and seller
        self.user = User.objects.create_user(
            email='seller@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Seller',
            role='seller'
        )
        self.seller = SellerProfile.objects.create(
            user=self.user,
            shop_name='Test Business',
            business_registration_number='REG123',
            tax_identification_number='TAX456',
            approval_status='approved'
        )
        
        # Create test product
        self.category = Category.objects.create(name='Test Category')
        self.product_type = ProductType.objects.create(name='Test Type')
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            category=self.category,
            product_type=self.product_type,
            seller=self.seller,
            price=100.00,
            status='published'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def create_test_image(self, width=100, height=100, format='JPEG', size_kb=None):
        """Create a test image file."""
        image = Image.new('RGB', (width, height), color='red')
        image_io = BytesIO()
        
        if size_kb:
            # Adjust quality to approximate desired file size
            quality = 95 if size_kb < 500 else 85 if size_kb < 1000 else 75
            image.save(image_io, format=format, quality=quality)
        else:
            image.save(image_io, format=format)
        
        image_io.seek(0)
        
        extension = 'jpg' if format == 'JPEG' else format.lower()
        return SimpleUploadedFile(
            f'test_image.{extension}',
            image_io.getvalue(),
            content_type=f'image/{extension}'
        )
    
    @patch('cloudinary.uploader.upload')
    def test_successful_image_upload(self, mock_upload):
        """Test successful image upload to Cloudinary."""
        # Mock Cloudinary response
        mock_upload.return_value = {
            'public_id': 'test_image_123',
            'secure_url': 'https://res.cloudinary.com/test/image/upload/test_image_123.jpg',
            'format': 'jpg',
            'bytes': 1024,
            'width': 100,
            'height': 100
        }
        
        image = self.create_test_image()
        
        response = self.client.post(
            f'/api/catalog/seller/products/{self.product.id}/images/',
            data={
                'image': image,
                'alt_text': 'Test alt text',
                'is_primary': True
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('image_url', response.data)
        self.assertEqual(response.data['alt_text'], 'Test alt text')
        self.assertTrue(response.data['is_primary'])
        
        # Verify Cloudinary upload was called
        mock_upload.assert_called_once()
    
    def test_invalid_file_type_rejection(self):
        """Test rejection of invalid file types."""
        # Create a text file instead of image
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'This is not an image',
            content_type='text/plain'
        )
        
        response = self.client.post(
            f'/api/catalog/seller/products/{self.product.id}/images/',
            data={
                'image': invalid_file,
                'alt_text': 'Invalid file'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)
    
    def test_file_size_limit_enforcement(self):
        """Test file size limit enforcement."""
        # Create a large image (>5MB)
        large_image = self.create_test_image(width=5000, height=5000, size_kb=6000)
        
        response = self.client.post(
            f'/api/catalog/seller/products/{self.product.id}/images/',
            data={
                'image': large_image,
                'alt_text': 'Large image'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)
    
    @patch('cloudinary.uploader.upload')
    def test_set_primary_image(self, mock_upload):
        """Test setting an image as primary."""
        # Mock Cloudinary response
        mock_upload.return_value = {
            'public_id': 'test_image_123',
            'secure_url': 'https://res.cloudinary.com/test/image/upload/test_image_123.jpg',
            'format': 'jpg',
            'bytes': 1024,
            'width': 100,
            'height': 100
        }
        
        # Create first image
        image1 = ProductImage.objects.create(
            product=self.product,
            image='test1.jpg',
            alt_text='Image 1',
            is_primary=True
        )
        
        # Create second image
        image2 = self.create_test_image()
        
        response = self.client.post(
            f'/api/catalog/seller/products/{self.product.id}/images/',
            data={
                'image': image2,
                'alt_text': 'Image 2',
                'is_primary': True
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that first image is no longer primary
        image1.refresh_from_db()
        self.assertFalse(image1.is_primary)
    
    @patch('cloudinary.uploader.upload')
    def test_set_primary_action(self, mock_upload):
        """Test set-primary action endpoint."""
        # Create test image
        image = ProductImage.objects.create(
            product=self.product,
            image='test.jpg',
            alt_text='Test image',
            is_primary=False
        )
        
        response = self.client.patch(
            f'/api/catalog/seller/products/{self.product.id}/images/{image.id}/set-primary/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Image set as primary successfully')
        
        # Verify image is now primary
        image.refresh_from_db()
        self.assertTrue(image.is_primary)
    
    def test_unauthorized_access_prevention(self):
        """Test prevention of unauthorized access."""
        # Create another seller
        other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            role='seller'
        )
        other_seller = SellerProfile.objects.create(
            user=other_user,
            shop_name='Other Business',
            business_registration_number='OTHER123',
            tax_identification_number='TAX789',
            approval_status='approved'
        )
        
        # Create product for other seller
        other_product = Product.objects.create(
            name='Other Product',
            description='Other Description',
            category=self.category,
            product_type=self.product_type,
            seller=other_seller,
            price=200.00,
            status='published'
        )
        
        # Try to upload image to other seller's product
        image = self.create_test_image()
        
        response = self.client.post(
            f'/api/catalog/seller/products/{other_product.id}/images/',
            data={
                'image': image,
                'alt_text': 'Unauthorized upload'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('cloudinary.uploader.upload')
    @patch('cloudinary.uploader.destroy')
    def test_image_deletion_with_cloudinary_cleanup(self, mock_destroy, mock_upload):
        """Test image deletion with Cloudinary cleanup."""
        # Mock Cloudinary responses
        mock_upload.return_value = {
            'public_id': 'test_image_123',
            'secure_url': 'https://res.cloudinary.com/test/image/upload/test_image_123.jpg'
        }
        mock_destroy.return_value = {'result': 'ok'}
        
        # Create image
        image = self.create_test_image()
        
        create_response = self.client.post(
            f'/api/catalog/seller/products/{self.product.id}/images/',
            data={
                'image': image,
                'alt_text': 'Test image'
            },
            format='multipart'
        )
        
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        image_id = create_response.data['id']
        
        # Delete image
        delete_response = self.client.delete(
            f'/api/catalog/seller/products/{self.product.id}/images/{image_id}/'
        )
        
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify Cloudinary destroy was called
        mock_destroy.assert_called_once()


class CloudinaryConfigurationTestCase(TestCase):
    """Test Cloudinary configuration."""
    
    def test_cloudinary_settings_configured(self):
        """Test that Cloudinary settings are properly configured."""
        from django.conf import settings
        
        # Check that cloudinary apps are in INSTALLED_APPS
        self.assertIn('cloudinary_storage', settings.INSTALLED_APPS)
        self.assertIn('cloudinary', settings.INSTALLED_APPS)
        
        # Check that cloudinary is imported without errors
        try:
            import cloudinary
            import cloudinary_storage
        except ImportError:
            self.fail("Cloudinary packages not installed properly")
    
    @patch.dict('os.environ', {'CLOUDINARY_URL': 'cloudinary://key:secret@cloud'})
    def test_cloudinary_url_parsing(self):
        """Test Cloudinary URL parsing from environment."""
        from african_back_end.settings.base import cloudinary
        
        # This test verifies that cloudinary configuration loads properly
        self.assertIsNotNone(cloudinary.config())


class ProductImageModelTestCase(TestCase):
    """Test ProductImage model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            role='seller'
        )
        self.seller = SellerProfile.objects.create(
            user=self.user,
            shop_name='Test Business',
            business_registration_number='REG123',
            tax_identification_number='TAX456',
            approval_status='approved'
        )
        self.category = Category.objects.create(name='Test Category')
        self.product_type = ProductType.objects.create(name='Test Type')
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            category=self.category,
            product_type=self.product_type,
            seller=self.seller,
            price=100.00,
            status='published'
        )
    
    def test_only_one_primary_image_per_product(self):
        """Test that only one image can be primary per product."""
        # Create first primary image
        image1 = ProductImage.objects.create(
            product=self.product,
            image='test1.jpg',
            alt_text='Image 1',
            is_primary=True
        )
        
        # Create second primary image
        image2 = ProductImage.objects.create(
            product=self.product,
            image='test2.jpg',
            alt_text='Image 2',
            is_primary=True
        )
        
        # First image should no longer be primary
        image1.refresh_from_db()
        self.assertFalse(image1.is_primary)
        self.assertTrue(image2.is_primary)
    
    def test_image_ordering(self):
        """Test image ordering by is_primary and created_at."""
        # Create images
        image1 = ProductImage.objects.create(
            product=self.product,
            image='test1.jpg',
            alt_text='Image 1',
            is_primary=False
        )
        image2 = ProductImage.objects.create(
            product=self.product,
            image='test2.jpg',
            alt_text='Image 2',
            is_primary=True
        )
        image3 = ProductImage.objects.create(
            product=self.product,
            image='test3.jpg',
            alt_text='Image 3',
            is_primary=False
        )
        
        # Get ordered images
        images = ProductImage.objects.filter(product=self.product).order_by('-is_primary', 'created_at')
        
        # Primary image should be first
        self.assertEqual(images[0], image2)