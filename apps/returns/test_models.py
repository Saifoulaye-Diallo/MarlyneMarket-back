from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import ReturnRequest
from apps.orders.models import Order, OrderItem
from apps.catalog.models import Product, Category, ProductType
from apps.accounts.models import SellerProfile
from decimal import Decimal

User = get_user_model()


class ReturnRequestModelTest(TestCase):
    """Tests pour le modèle ReturnRequest"""
    
    def setUp(self):
        # Setup
        seller_user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            role='seller'
        )
        self.seller = SellerProfile.objects.create(
            user=seller_user,
            shop_name='Test Shop'
        )
        
        category = Category.objects.create(name='Test', slug='test')
        ptype = ProductType.objects.create(name='Test')
        
        product = Product.objects.create(
            seller=self.seller,
            category=category,
            product_type=ptype,
            name='Test Product',
            description='Test',
            price=Decimal('99.99')
        )
        
        customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123',
            role='customer'
        )
        
        order = Order.objects.create(
            user=customer,
            subtotal=Decimal('99.99'),
            tax=Decimal('0.00'),
            shipping_fee=Decimal('0.00')
        )
        
        self.order_item = OrderItem.objects.create(
            order=order,
            product=product,
            seller=self.seller,
            title_snapshot='Test Product',
            price_snapshot=Decimal('99.99'),
            quantity=1
        )
        
        self.customer = customer
        
        # Créer return
        self.return_request = ReturnRequest.objects.create(
            order_item=self.order_item,
            user=customer,
            seller=self.seller,
            reason='defective',
            description='Item arrived broken',
            status='pending'
        )
    
    def test_return_creation(self):
        self.assertEqual(self.return_request.order_item, self.order_item)
        self.assertEqual(self.return_request.user, self.customer)
        self.assertEqual(self.return_request.seller, self.seller)
        self.assertEqual(self.return_request.reason, 'defective')
        self.assertEqual(self.return_request.status, 'pending')
    
    def test_return_statuses(self):
        valid_statuses = ['pending', 'approved', 'rejected', 'shipped', 'received']
        for status in valid_statuses:
            self.return_request.status = status
            self.return_request.save()
            self.return_request.refresh_from_db()
            self.assertEqual(self.return_request.status, status)
    
    def test_refund_status(self):
        valid_refund_statuses = ['pending', 'approved', 'rejected', 'paid', 'failed']
        for refund_status in valid_refund_statuses:
            self.return_request.refund_status = refund_status
            self.return_request.save()
            self.return_request.refresh_from_db()
            self.assertEqual(self.return_request.refund_status, refund_status)
    
    def test_refund_amount(self):
        self.return_request.refund_amount = Decimal('99.99')
        self.return_request.refund_status = 'approved'
        self.return_request.save()
        
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.refund_amount, Decimal('99.99'))
    
    def test_deduction_amount(self):
        self.return_request.refund_amount = Decimal('99.99')
        self.return_request.deduction_amount = Decimal('10.00')
        self.return_request.deduction_reason = 'Restocking fee'
        self.return_request.save()
        
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.deduction_amount, Decimal('10.00'))
        self.assertEqual(self.return_request.deduction_reason, 'Restocking fee')
    
    def test_inspection_fields(self):
        inspector = User.objects.create_user(
            username='inspector',
            email='inspector@example.com',
            password='pass123'
        )
        
        from django.utils import timezone
        self.return_request.inspected_by = inspector
        self.return_request.inspected_at = timezone.now()
        self.return_request.inspection_notes = 'Item is broken'
        self.return_request.save()
        
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.inspected_by, inspector)
        self.assertIsNotNone(self.return_request.inspected_at)
        self.assertEqual(self.return_request.inspection_notes, 'Item is broken')
    
    def test_shipping_tracking(self):
        self.return_request.tracking_number = 'TRACK123'
        self.return_request.carrier = 'FedEx'
        self.return_request.save()
        
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.tracking_number, 'TRACK123')
        self.assertEqual(self.return_request.carrier, 'FedEx')
    
    def test_return_reasons(self):
        valid_reasons = ['defective', 'not_as_described', 'damaged', 'wrong_item', 'changed_mind']
        for reason in valid_reasons:
            self.return_request.reason = reason
            self.return_request.save()
            self.return_request.refresh_from_db()
            self.assertEqual(self.return_request.reason, reason)
    
    def test_response_tracking(self):
        responder = User.objects.create_user(
            username='responder',
            email='responder@example.com',
            password='pass123'
        )
        
        self.return_request.responded_by = responder
        self.return_request.response_note = 'Return approved'
        self.return_request.save()
        
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.responded_by, responder)
        self.assertEqual(self.return_request.response_note, 'Return approved')
