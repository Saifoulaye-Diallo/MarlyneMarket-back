from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Order, OrderItem, SellerOrder
from apps.catalog.models import Product, Category, ProductType
from apps.accounts.models import SellerProfile
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class OrderModelTest(TestCase):
    """Tests pour le modèle Order"""
    
    def setUp(self):
        # Setup customer
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123',
            role='customer'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00'),
            discount=Decimal('0.00'),
            status='pending',
            payment_status='unpaid'
        )
    
    def test_order_creation(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.subtotal, Decimal('100.00'))
        self.assertIsNotNone(self.order.reference)
    
    def test_order_status(self):
        valid_statuses = ['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
        for status in valid_statuses:
            self.order.status = status
            self.order.save()
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, status)
    
    def test_payment_status(self):
        valid_payment_statuses = ['unpaid', 'paid', 'failed', 'refunded']
        for pstatus in valid_payment_statuses:
            self.order.payment_status = pstatus
            self.order.save()
            self.order.refresh_from_db()
            self.assertEqual(self.order.payment_status, pstatus)
    
    def test_order_discounts(self):
        self.order.discount = Decimal('10.00')
        self.order.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.discount, Decimal('10.00'))
    
    def test_order_notes(self):
        self.order.notes = "Special handling"
        self.order.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.notes, "Special handling")
    
    def test_shipping_address_json(self):
        address = {"city": "Paris", "country": "France"}
        self.order.shipping_address_json = address
        self.order.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.shipping_address_json, address)


class OrderItemModelTest(TestCase):
    """Tests pour le modèle OrderItem"""
    
    def setUp(self):
        # Create seller
        seller_user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            role='seller'
        )
        self.seller = SellerProfile.objects.create(user=seller_user)
        
        # Create product
        product_type = ProductType.objects.create(name='Electronics')
        category = Category.objects.create(name='Phones', slug='phones')
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=Decimal('50.00'),
            seller=self.seller,
            category=category,
            product_type=product_type
        )
        
        # Create customer and order
        customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123'
        )
        
        self.order = Order.objects.create(
            user=customer,
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
    
    def test_order_item_creation(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            seller=self.seller,
            title_snapshot=self.product.name,
            price_snapshot=self.product.price,
            quantity=2
        )
        self.assertEqual(item.order, self.order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)
    
    def test_order_item_quantity(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            seller=self.seller,
            title_snapshot=self.product.name,
            price_snapshot=self.product.price,
            quantity=5
        )
        item.quantity = 10
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.quantity, 10)
    
    def test_order_item_snapshots(self):
        """Test que les snapshots conservent les prix à la commande"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            seller=self.seller,
            title_snapshot=self.product.name,
            price_snapshot=Decimal('45.00'),
            quantity=2
        )
        # Le produit change de prix mais l'article conserve le prix de commande
        self.product.price = Decimal('60.00')
        self.product.save()
        item.refresh_from_db()
        self.assertEqual(item.price_snapshot, Decimal('45.00'))


class SellerOrderModelTest(TestCase):
    """Tests pour le modèle SellerOrder"""
    
    def setUp(self):
        # Create seller
        seller_user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            role='seller'
        )
        self.seller = SellerProfile.objects.create(user=seller_user)
        
        # Create product
        product_type = ProductType.objects.create(name='Electronics')
        category = Category.objects.create(name='Phones', slug='phones')
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=Decimal('50.00'),
            seller=self.seller,
            category=category,
            product_type=product_type
        )
        
        # Create customer and order
        customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123'
        )
        
        self.order = Order.objects.create(
            user=customer,
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
        
        # Create seller order
        self.seller_order = SellerOrder.objects.create(
            order=self.order,
            seller=self.seller
        )
    
    def test_seller_order_creation(self):
        self.assertEqual(self.seller_order.order, self.order)
        self.assertEqual(self.seller_order.seller, self.seller)
    
    def test_seller_order_statuses(self):
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        for status in valid_statuses:
            self.seller_order.status = status
            self.seller_order.save()
            self.seller_order.refresh_from_db()
            self.assertEqual(self.seller_order.status, status)
    
    def test_seller_order_tracking(self):
        self.seller_order.tracking_number = "TRACK123"
        self.seller_order.tracking_carrier = "UPS"
        self.seller_order.save()
        self.seller_order.refresh_from_db()
        self.assertEqual(self.seller_order.tracking_number, "TRACK123")
        self.assertEqual(self.seller_order.tracking_carrier, "UPS")
    
    def test_seller_order_shipping_dates(self):
        now = timezone.now()
        self.seller_order.shipped_at = now
        self.seller_order.save()
        self.seller_order.refresh_from_db()
        self.assertIsNotNone(self.seller_order.shipped_at)
