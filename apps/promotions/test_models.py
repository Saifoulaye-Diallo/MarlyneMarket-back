from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Coupon, CouponUsage
from apps.orders.models import Order
from apps.catalog.models import Category, Product, ProductType
from apps.accounts.models import SellerProfile
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class CouponModelTest(TestCase):
    """Tests pour le modèle Coupon"""
    
    def setUp(self):
        # Setup
        now = timezone.now()
        
        self.coupon = Coupon.objects.create(
            code='SAVE10',
            name='Save 10%',
            discount_type='percentage',
            discount_value=Decimal('10'),
            status='active',
            start_date=now,
            end_date=now + timezone.timedelta(days=30)
        )
    
    def test_coupon_creation(self):
        self.assertEqual(self.coupon.code, 'SAVE10')
        self.assertEqual(self.coupon.name, 'Save 10%')
        self.assertEqual(self.coupon.discount_type, 'percentage')
        self.assertEqual(self.coupon.discount_value, Decimal('10'))
        self.assertEqual(self.coupon.status, 'active')
    
    def test_coupon_defaults(self):
        self.assertTrue(self.coupon.is_active)
    
    def test_coupon_statuses(self):
        valid_statuses = ['active', 'inactive', 'draft', 'expired']
        for status in valid_statuses:
            self.coupon.status = status
            self.coupon.save()
            self.coupon.refresh_from_db()
            self.assertEqual(self.coupon.status, status)
    
    def test_discount_types(self):
        valid_types = ['percentage', 'fixed']
        for dtype in valid_types:
            self.coupon.discount_type = dtype
            self.coupon.save()
            self.coupon.refresh_from_db()
            self.assertEqual(self.coupon.discount_type, dtype)
    
    def test_coupon_usage_limits(self):
        self.coupon.usage_limit = 100
        self.coupon.usage_limit_per_user = 5
        self.coupon.save()
        
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.usage_limit, 100)
        self.assertEqual(self.coupon.usage_limit_per_user, 5)
    
    def test_coupon_purchase_limits(self):
        self.coupon.min_purchase_amount = Decimal('50.00')
        self.coupon.max_purchase_amount = Decimal('500.00')
        self.coupon.save()
        
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.min_purchase_amount, Decimal('50.00'))
        self.assertEqual(self.coupon.max_purchase_amount, Decimal('500.00'))
    
    def test_coupon_validity_dates(self):
        now = timezone.now()
        self.coupon.start_date = now
        self.coupon.end_date = now + timezone.timedelta(days=30)
        self.coupon.save()
        
        self.coupon.refresh_from_db()
        self.assertIsNotNone(self.coupon.start_date)
        self.assertIsNotNone(self.coupon.end_date)
    
    def test_coupon_stackable(self):
        self.coupon.is_stackable = True
        self.coupon.save()
        
        self.coupon.refresh_from_db()
        self.assertTrue(self.coupon.is_stackable)
    
    def test_coupon_str(self):
        expected = f"SAVE10 - Save 10%"
        self.assertEqual(str(self.coupon), expected)


class CouponUsageModelTest(TestCase):
    """Tests pour le modèle CouponUsage"""
    
    def setUp(self):
        # Setup coupon
        now = timezone.now()
        
        self.coupon = Coupon.objects.create(
            code='SAVE10',
            name='Save 10%',
            discount_type='percentage',
            discount_value=Decimal('10'),
            start_date=now,
            end_date=now + timezone.timedelta(days=30)
        )
        
        # Setup user
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123'
        )
        
        self.usage = CouponUsage.objects.create(
            coupon=self.coupon,
            user=self.user
        )
    
    def test_usage_creation(self):
        self.assertEqual(self.usage.coupon, self.coupon)
        self.assertEqual(self.usage.user, self.user)
    
    def test_usage_refund_tracking(self):
        self.usage.is_refunded = True
        self.usage.refund_amount = Decimal('10.00')
        self.usage.save()
        
        self.usage.refresh_from_db()
        self.assertTrue(self.usage.is_refunded)
        self.assertEqual(self.usage.refund_amount, Decimal('10.00'))
    
    def test_usage_refund_date(self):
        now = timezone.now()
        self.usage.refunded_at = now
        self.usage.save()
        
        self.usage.refresh_from_db()
        self.assertIsNotNone(self.usage.refunded_at)
    
    def test_multiple_usages(self):
        """Test that multiple usages are tracked"""
        usage2 = CouponUsage.objects.create(
            coupon=self.coupon,
            user=self.user
        )
        
        usages = CouponUsage.objects.filter(coupon=self.coupon)
        self.assertEqual(usages.count(), 2)
    
    def test_usage_per_user_tracking(self):
        """Test tracking usage per user"""
        usages = CouponUsage.objects.filter(
            coupon=self.coupon,
            user=self.user
        )
        self.assertEqual(usages.count(), 1)
