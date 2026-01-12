from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Payment, Refund
from apps.orders.models import Order
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class PaymentModelTest(TestCase):
    """Tests pour le modèle Payment"""
    
    def setUp(self):
        # Create user and order
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('130.00'),
            provider='stripe',
            status='pending'
        )
    
    def test_payment_creation(self):
        self.assertEqual(self.payment.order, self.order)
        self.assertEqual(self.payment.amount, Decimal('130.00'))
        self.assertEqual(self.payment.provider, 'stripe')
        self.assertEqual(self.payment.status, 'pending')
    
    def test_payment_providers(self):
        valid_providers = ['stripe', 'paypal', 'manual']
        for provider in valid_providers:
            self.payment.provider = provider
            self.payment.save()
            self.payment.refresh_from_db()
            self.assertEqual(self.payment.provider, provider)
    
    def test_payment_statuses(self):
        valid_statuses = ['pending', 'processing', 'succeeded', 'failed', 'cancelled']
        for status in valid_statuses:
            self.payment.status = status
            self.payment.save()
            self.payment.refresh_from_db()
            self.assertEqual(self.payment.status, status)
    
    def test_payment_success(self):
        self.payment.status = 'succeeded'
        self.payment.paid_at = timezone.now()
        self.payment.save()
        
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'succeeded')
        self.assertIsNotNone(self.payment.paid_at)
    
    def test_payment_error_message(self):
        self.payment.status = 'failed'
        self.payment.error_message = 'Card declined'
        self.payment.save()
        
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')
        self.assertEqual(self.payment.error_message, 'Card declined')
    
    def test_payment_metadata(self):
        metadata = {'ip': '192.168.1.1', 'device': 'mobile'}
        self.payment.metadata = metadata
        self.payment.save()
        
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.metadata, metadata)
    
    def test_payment_paid_at(self):
        now = timezone.now()
        self.payment.paid_at = now
        self.payment.save()
        
        self.payment.refresh_from_db()
        self.assertIsNotNone(self.payment.paid_at)
    
    def test_payment_client_secret(self):
        self.payment.client_secret = 'pi_test_secret_123'
        self.payment.save()
        
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.client_secret, 'pi_test_secret_123')


class RefundModelTest(TestCase):
    """Tests pour le modèle Refund"""
    
    def setUp(self):
        # Create user and order
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('130.00'),
            provider='stripe',
            status='succeeded'
        )
        
        self.refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('130.00'),
            status='pending'
        )
    
    def test_refund_creation(self):
        self.assertEqual(self.refund.payment, self.payment)
        self.assertEqual(self.refund.amount, Decimal('130.00'))
        self.assertEqual(self.refund.status, 'pending')
    
    def test_refund_statuses(self):
        valid_statuses = ['pending', 'succeeded', 'failed', 'cancelled']
        for status in valid_statuses:
            self.refund.status = status
            self.refund.save()
            self.refund.refresh_from_db()
            self.assertEqual(self.refund.status, status)
    
    def test_refund_provider_id(self):
        self.refund.provider_refund_id = 're_test123'
        self.refund.save()
        
        self.refund.refresh_from_db()
        self.assertEqual(self.refund.provider_refund_id, 're_test123')
    
    def test_refund_initiated_by(self):
        self.refund.initiated_by = self.user
        self.refund.save()
        
        self.refund.refresh_from_db()
        self.assertEqual(self.refund.initiated_by, self.user)
    
    def test_multiple_refunds(self):
        """Test multiple refunds for same payment"""
        refund2 = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('50.00'),
            status='pending'
        )
        
        refunds = Refund.objects.filter(payment=self.payment)
        self.assertEqual(refunds.count(), 2)
    
    def test_refund_reasons(self):
        self.refund.reason = 'Customer requested refund'
        self.refund.save()
        
        self.refund.refresh_from_db()
        self.assertEqual(self.refund.reason, 'Customer requested refund')
