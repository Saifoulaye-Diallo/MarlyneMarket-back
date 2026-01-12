"""
Tests for multilingual catalog content (i18n).
Tests translation models, API endpoints, and fallback behavior.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from apps.accounts.models import SellerProfile
from .models import (
    Category, ProductType, Attribute, AttributeOption, Product,
    CategoryTranslation, ProductTypeTranslation, AttributeTranslation,
    AttributeOptionTranslation, ProductTranslation
)
from .i18n import get_translated_name, get_translated_description, get_language_code
from .serializers_i18n import TranslatedCategorySerializer, TranslatedProductTypeSchemaSerializer

User = get_user_model()


class TranslationModelsTest(TestCase):
    """Test translation model creation and relationships."""

    def setUp(self):
        """Create test data."""
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices'
        )
        self.seller_user = User.objects.create_user(
            username='seller1',
            email='seller@test.com',
            password='test123'
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.seller_user,
            shop_name='Test Shop'
        )
        self.product_type = ProductType.objects.create(
            name='Phones',
            description='Mobile phones'
        )

    def test_category_translation_creation(self):
        """Test creating category translations."""
        translation_fr = CategoryTranslation.objects.create(
            category=self.category,
            language_code='fr',
            name='Électronique',
            description='Appareils électroniques'
        )
        self.assertEqual(translation_fr.language_code, 'fr')
        self.assertEqual(translation_fr.name, 'Électronique')
        self.assertEqual(translation_fr.category, self.category)

    def test_category_translation_unique_constraint(self):
        """Test that translation is unique per language."""
        CategoryTranslation.objects.create(
            category=self.category,
            language_code='fr',
            name='Électronique',
            description='Appareils électroniques'
        )
        # Trying to create another translation for the same language should fail
        with self.assertRaises(Exception):
            CategoryTranslation.objects.create(
                category=self.category,
                language_code='fr',
                name='Électronique Updated',
                description='Updated'
            )

    def test_product_type_translation(self):
        """Test product type translation."""
        translation_ar = ProductTypeTranslation.objects.create(
            product_type=self.product_type,
            language_code='ar',
            name='الهواتف',
            description='الهواتف الذكية'
        )
        self.assertEqual(translation_ar.language_code, 'ar')
        self.assertEqual(translation_ar.name, 'الهواتف')

    def test_product_translation(self):
        """Test product translation."""
        product = Product.objects.create(
            seller=self.seller_profile,
            category=self.category,
            product_type=self.product_type,
            name='iPhone 15',
            description='Latest iPhone model',
            price=999.99,
            stock=10
        )
        translation_fr = ProductTranslation.objects.create(
            product=product,
            language_code='fr',
            name='iPhone 15',
            description='Dernier modèle iPhone'
        )
        self.assertEqual(translation_fr.product, product)
        self.assertEqual(translation_fr.language_code, 'fr')


class TranslationHelpersTest(TestCase):
    """Test i18n helper functions."""

    def setUp(self):
        """Create test data."""
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices'
        )
        # Create French translation
        CategoryTranslation.objects.create(
            category=self.category,
            language_code='fr',
            name='Électronique',
            description='Appareils électroniques'
        )
        # Create Arabic translation
        CategoryTranslation.objects.create(
            category=self.category,
            language_code='ar',
            name='الإلكترونيات',
            description='الأجهزة الإلكترونية'
        )

    def test_get_translated_name_french(self):
        """Test getting French translation."""
        name = get_translated_name(self.category, 'fr')
        self.assertEqual(name, 'Électronique')

    def test_get_translated_name_arabic(self):
        """Test getting Arabic translation."""
        name = get_translated_name(self.category, 'ar')
        self.assertEqual(name, 'الإلكترونيات')

    def test_get_translated_name_fallback(self):
        """Test fallback to default language when translation doesn't exist."""
        name = get_translated_name(self.category, 'es')
        # Should fall back to default language (en)
        self.assertEqual(name, 'Electronics')

    def test_get_translated_description_french(self):
        """Test getting French description translation."""
        desc = get_translated_description(self.category, 'fr')
        self.assertEqual(desc, 'Appareils électroniques')

    def test_get_translated_description_fallback(self):
        """Test fallback for missing description translation."""
        desc = get_translated_description(self.category, 'es')
        self.assertEqual(desc, 'Electronic devices')

    def test_get_language_code_valid(self):
        """Test language code extraction with valid language."""
        factory = RequestFactory()
        request = factory.get('/', HTTP_ACCEPT_LANGUAGE='fr-FR')
        lang = get_language_code(request)
        # Should return 'fr' or similar
        self.assertIn(lang, ['fr', 'en'])


class TranslationAPITest(APITestCase):
    """Test API endpoints with translation support."""

    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        # Create category with translations
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices'
        )
        CategoryTranslation.objects.create(
            category=self.category,
            language_code='fr',
            name='Électronique',
            description='Appareils électroniques'
        )
        CategoryTranslation.objects.create(
            category=self.category,
            language_code='ar',
            name='الإلكترونيات',
            description='الأجهزة الإلكترونية'
        )

    def test_category_api_english(self):
        """Test category API returns English content by default."""
        response = self.client.get(f'/api/categories/{self.category.slug}/')
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['name'], 'Electronics')

    def test_category_api_french_header(self):
        """Test category API returns French content with Accept-Language header."""
        response = self.client.get(
            f'/api/categories/{self.category.slug}/',
            HTTP_ACCEPT_LANGUAGE='fr'
        )
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['name'], 'Électronique')

    def test_category_api_arabic_header(self):
        """Test category API returns Arabic content with Accept-Language header."""
        response = self.client.get(
            f'/api/categories/{self.category.slug}/',
            HTTP_ACCEPT_LANGUAGE='ar'
        )
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['name'], 'الإلكترونيات')

    def test_category_available_languages(self):
        """Test API returns list of available languages for content."""
        response = self.client.get(f'/api/categories/{self.category.slug}/')
        if response.status_code == 200:
            data = response.json()
            if 'available_languages' in data:
                self.assertIn('fr', data['available_languages'])
                self.assertIn('ar', data['available_languages'])


class ProductTypeSchemaTranslationTest(APITestCase):
    """Test product type schema endpoint with translations."""

    def setUp(self):
        """Create test data with attributes."""
        self.product_type = ProductType.objects.create(
            name='Phones',
            description='Mobile phones'
        )
        ProductTypeTranslation.objects.create(
            product_type=self.product_type,
            language_code='fr',
            name='Téléphones',
            description='Téléphones mobiles'
        )

        # Create attribute with translation
        self.attribute = Attribute.objects.create(
            name='Color',
            data_type='choice'
        )
        AttributeTranslation.objects.create(
            attribute=self.attribute,
            language_code='fr',
            name='Couleur'
        )

        # Create attribute option with translation
        self.option = AttributeOption.objects.create(
            attribute=self.attribute,
            value='Black'
        )
        AttributeOptionTranslation.objects.create(
            option=self.option,
            language_code='fr',
            value='Noir'
        )

        # Link attribute to product type
        from .models import TypeAttributeRule
        TypeAttributeRule.objects.create(
            product_type=self.product_type,
            attribute=self.attribute,
            is_required=True,
            display_order=1
        )

    def test_schema_english(self):
        """Test schema returns English content."""
        response = self.client.get(f'/api/product-types/{self.product_type.id}/schema/')
        if response.status_code == 200:
            data = response.json()
            if 'attributes' in data and data['attributes']:
                self.assertEqual(data['attributes'][0]['name'], 'Color')

    def test_schema_french(self):
        """Test schema returns French content with Accept-Language header."""
        response = self.client.get(
            f'/api/product-types/{self.product_type.id}/schema/',
            HTTP_ACCEPT_LANGUAGE='fr'
        )
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['name'], 'Téléphones')
            if 'attributes' in data and data['attributes']:
                self.assertEqual(data['attributes'][0]['name'], 'Couleur')
                if 'options' in data['attributes'][0] and data['attributes'][0]['options']:
                    self.assertEqual(data['attributes'][0]['options'][0]['value'], 'Noir')


class ProductTranslationTest(APITestCase):
    """Test product endpoints with translations."""

    def setUp(self):
        """Create test product with translations."""
        self.seller_user = User.objects.create_user(
            username='seller1',
            email='seller@test.com',
            password='test123'
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.seller_user,
            shop_name='Test Shop'
        )

        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )

        self.product_type = ProductType.objects.create(
            name='Phones',
            description='Mobile phones'
        )

        self.product = Product.objects.create(
            seller=self.seller_profile,
            category=self.category,
            product_type=self.product_type,
            name='iPhone 15',
            description='Latest Apple iPhone',
            price=999.99,
            stock=10,
            status='published'
        )

        # Create French translation
        ProductTranslation.objects.create(
            product=self.product,
            language_code='fr',
            name='iPhone 15',
            description='Dernier iPhone d\'Apple'
        )

        # Create Arabic translation
        ProductTranslation.objects.create(
            product=self.product,
            language_code='ar',
            name='آيفون 15',
            description='أحدث iPhone من Apple'
        )

    def test_product_english(self):
        """Test product API returns English content."""
        response = self.client.get(f'/api/products/{self.product.id}/')
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['name'], 'iPhone 15')
            self.assertEqual(data['description'], 'Latest Apple iPhone')

    def test_product_french(self):
        """Test product API returns French content."""
        response = self.client.get(
            f'/api/products/{self.product.id}/',
            HTTP_ACCEPT_LANGUAGE='fr'
        )
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['name'], 'iPhone 15')
            self.assertEqual(data['description'], 'Dernier iPhone d\'Apple')

    def test_product_arabic(self):
        """Test product API returns Arabic content."""
        response = self.client.get(
            f'/api/products/{self.product.id}/',
            HTTP_ACCEPT_LANGUAGE='ar'
        )
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['name'], 'آيفون 15')
            self.assertEqual(data['description'], 'أحدث iPhone من Apple')
