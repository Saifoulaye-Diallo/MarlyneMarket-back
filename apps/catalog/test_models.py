from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import (
    Category, ProductType, Attribute, AttributeOption,
    TypeAttributeRule, Product, ProductImage, ProductAttributeValue
)
from apps.accounts.models import SellerProfile
from decimal import Decimal

User = get_user_model()


class CategoryModelTest(TestCase):
    """Tests pour le modèle Category"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices'
        )
    
    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Electronics')
        self.assertEqual(self.category.slug, 'electronics')
        self.assertTrue(self.category.is_active)
    
    def test_category_str(self):
        self.assertEqual(str(self.category), 'Electronics')
    
    def test_category_unique_slug(self):
        with self.assertRaises(Exception):
            Category.objects.create(
                name='Different',
                slug='electronics'
            )


class AttributeModelTest(TestCase):
    """Tests pour le modèle Attribute"""
    
    def test_attribute_text(self):
        attr = Attribute.objects.create(
            name='Color',
            data_type='text'
        )
        self.assertEqual(attr.data_type, 'text')
    
    def test_attribute_number(self):
        attr = Attribute.objects.create(
            name='Size',
            data_type='number'
        )
        self.assertEqual(attr.data_type, 'number')
    
    def test_attribute_choice(self):
        attr = Attribute.objects.create(
            name='Brand',
            data_type='choice'
        )
        self.assertEqual(attr.data_type, 'choice')
    
    def test_attribute_bool(self):
        attr = Attribute.objects.create(
            name='Waterproof',
            data_type='bool'
        )
        self.assertEqual(attr.data_type, 'bool')


class AttributeOptionModelTest(TestCase):
    """Tests pour le modèle AttributeOption"""
    
    def setUp(self):
        self.attribute = Attribute.objects.create(
            name='Color',
            data_type='choice'
        )
        self.option = AttributeOption.objects.create(
            attribute=self.attribute,
            value='Red'
        )
    
    def test_option_creation(self):
        self.assertEqual(self.option.value, 'Red')
        self.assertEqual(self.option.attribute, self.attribute)
    
    def test_option_str(self):
        expected = 'Color: Red'
        self.assertEqual(str(self.option), expected)


class ProductTypeModelTest(TestCase):
    """Tests pour le modèle ProductType"""
    
    def setUp(self):
        self.product_type = ProductType.objects.create(
            name='Electronics Device',
            description='Electronic devices like phones'
        )
        self.attribute = Attribute.objects.create(
            name='Brand',
            data_type='text'
        )
        self.rule = TypeAttributeRule.objects.create(
            product_type=self.product_type,
            attribute=self.attribute,
            is_required=True,
            display_order=1
        )
    
    def test_product_type_creation(self):
        self.assertEqual(self.product_type.name, 'Electronics Device')
        self.assertTrue(self.product_type.is_active)
    
    def test_attribute_rules(self):
        self.assertEqual(
            self.product_type.attribute_rules.count(),
            1
        )
        self.assertTrue(self.rule.is_required)


class ProductModelTest(TestCase):
    """Tests pour le modèle Product"""
    
    def setUp(self):
        # Créer un utilisateur vendeur
        user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            role='seller'
        )
        self.seller = SellerProfile.objects.create(
            user=user,
            shop_name='Test Shop'
        )
        
        # Créer category et type
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.product_type = ProductType.objects.create(
            name='Phone'
        )
        
        # Créer un produit
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            product_type=self.product_type,
            name='iPhone 15',
            description='Latest iPhone',
            price=Decimal('999.99'),
            stock=50,
            status='published'
        )
    
    def test_product_creation(self):
        self.assertEqual(self.product.name, 'iPhone 15')
        self.assertEqual(self.product.price, Decimal('999.99'))
        self.assertEqual(self.product.stock, 50)
    
    def test_product_status_choices(self):
        valid_statuses = ['draft', 'published', 'disabled']
        for status in valid_statuses:
            self.product.status = status
            self.product.save()
            self.product.refresh_from_db()
            self.assertEqual(self.product.status, status)
    
    def test_product_condition_choices(self):
        valid_conditions = ['new', 'like_new', 'used', 'refurbished']
        for condition in valid_conditions:
            self.product.condition = condition
            self.product.save()
            self.product.refresh_from_db()
            self.assertEqual(self.product.condition, condition)
    
    def test_product_discount_price(self):
        self.product.discount_percentage = 10
        self.product.save()
        self.product.refresh_from_db()
        
        effective = self.product.get_effective_price()
        expected = Decimal('999.99') * (Decimal('100') - Decimal('10')) / Decimal('100')
        self.assertEqual(effective, expected)
    
    def test_product_discount_fixed(self):
        self.product.discount_price = Decimal('899.99')
        self.product.save()
        
        effective = self.product.get_effective_price()
        self.assertEqual(effective, Decimal('899.99'))
    
    def test_product_str(self):
        expected = f"iPhone 15 ({self.seller.shop_name})"
        self.assertEqual(str(self.product), expected)
    
    def test_product_metrics(self):
        self.assertEqual(self.product.average_rating, 0)
        self.assertEqual(self.product.total_reviews, 0)
        self.assertEqual(self.product.total_sold, 0)
    
    def test_shipping_fields(self):
        self.product.shipping_weight = Decimal('0.5')
        self.product.shipping_cost = Decimal('5.99')
        self.product.save()
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.shipping_weight, Decimal('0.5'))
        self.assertEqual(self.product.shipping_cost, Decimal('5.99'))
    
    def test_seo_fields(self):
        self.product.meta_title = 'Best iPhone 15 Price'
        self.product.meta_description = 'Buy iPhone 15 at best price'
        self.product.meta_keywords = 'iphone, phone, apple'
        self.product.save()
        
        self.product.refresh_from_db()
        self.assertIsNotNone(self.product.meta_title)
        self.assertIsNotNone(self.product.meta_description)
        self.assertIsNotNone(self.product.meta_keywords)


class ProductImageModelTest(TestCase):
    """Tests pour le modèle ProductImage"""
    
    def setUp(self):
        user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            role='seller'
        )
        seller = SellerProfile.objects.create(
            user=user,
            shop_name='Test Shop'
        )
        category = Category.objects.create(name='Test', slug='test')
        ptype = ProductType.objects.create(name='Test')
        
        self.product = Product.objects.create(
            seller=seller,
            category=category,
            product_type=ptype,
            name='Test',
            description='Test',
            price=Decimal('99.99')
        )
        
        self.image = ProductImage.objects.create(
            product=self.product,
            image='products/test.jpg',
            is_primary=True
        )
    
    def test_image_creation(self):
        self.assertEqual(self.image.product, self.product)
        self.assertTrue(self.image.is_primary)
    
    def test_only_one_primary_image(self):
        """Test qu'une seule image peut être primaire"""
        image2 = ProductImage.objects.create(
            product=self.product,
            image='products/test2.jpg',
            is_primary=True
        )
        
        self.image.refresh_from_db()
        self.assertFalse(self.image.is_primary)
        self.assertTrue(image2.is_primary)


class ProductAttributeValueModelTest(TestCase):
    """Tests pour le modèle ProductAttributeValue"""
    
    def setUp(self):
        user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            role='seller'
        )
        seller = SellerProfile.objects.create(
            user=user,
            shop_name='Test Shop'
        )
        category = Category.objects.create(name='Test', slug='test')
        ptype = ProductType.objects.create(name='Test')
        
        self.product = Product.objects.create(
            seller=seller,
            category=category,
            product_type=ptype,
            name='Test',
            description='Test',
            price=Decimal('99.99')
        )
        
        self.color_attr = Attribute.objects.create(
            name='Color',
            data_type='text'
        )
    
    def test_text_attribute_value(self):
        attr_val = ProductAttributeValue.objects.create(
            product=self.product,
            attribute=self.color_attr,
            value_text='Red'
        )
        self.assertEqual(attr_val.get_value(), 'Red')
    
    def test_number_attribute_value(self):
        size_attr = Attribute.objects.create(
            name='Size',
            data_type='number'
        )
        attr_val = ProductAttributeValue.objects.create(
            product=self.product,
            attribute=size_attr,
            value_number=Decimal('42.5')
        )
        self.assertEqual(attr_val.get_value(), Decimal('42.5'))
