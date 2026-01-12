"""
Tests for the promotions app.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, SellerProfile
from apps.promotions.models import Coupon, CouponUsage
from apps.promotions.services import CouponService


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def customer_user(db):
    """Create a customer user."""
    return User.objects.create_user(
        username='customer',
        email='customer@test.com',
        password='testpass123',
        role='customer'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='testpass123',
    )


@pytest.fixture
def seller_user(db):
    """Create a seller user with profile."""
    user = User.objects.create_user(
        username='seller',
        email='seller@test.com',
        password='testpass123',
        role='seller'
    )
    SellerProfile.objects.create(
        user=user,
        shop_name='Test Shop',
        status='active'
    )
    return user


@pytest.fixture
def active_coupon(db, admin_user):
    """Create an active global coupon."""
    return Coupon.objects.create(
        code='SAVE20',
        discount_type='percentage',
        discount_value=Decimal('20'),
        min_purchase_amount=Decimal('50'),
        start_date=timezone.now() - timedelta(days=1),
        end_date=timezone.now() + timedelta(days=30),
        is_active=True,
        scope='global',
        created_by=admin_user,
    )


@pytest.mark.django_db
class TestCouponModel:
    """Tests for Coupon model."""
    
    def test_create_coupon(self, admin_user):
        """Test creating a coupon."""
        coupon = Coupon.objects.create(
            code='TEST10',
            discount_type='fixed',
            discount_value=Decimal('10'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            created_by=admin_user,
        )
        
        assert coupon.pk is not None
        assert coupon.code == 'TEST10'
        assert coupon.is_valid is True
    
    def test_expired_coupon_invalid(self, admin_user):
        """Test expired coupon is not valid."""
        coupon = Coupon.objects.create(
            code='EXPIRED',
            discount_type='percentage',
            discount_value=Decimal('10'),
            start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now() - timedelta(days=1),
            created_by=admin_user,
        )
        
        assert coupon.is_valid is False
    
    def test_usage_limit_reached(self, admin_user):
        """Test coupon with usage limit reached."""
        coupon = Coupon.objects.create(
            code='LIMITED',
            discount_type='percentage',
            discount_value=Decimal('10'),
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=7),
            usage_limit=10,
            times_used=10,
            created_by=admin_user,
        )
        
        assert coupon.is_valid is False


@pytest.mark.django_db
class TestCouponService:
    """Tests for CouponService."""
    
    def test_validate_valid_coupon(self, active_coupon, customer_user):
        """Test validating a valid coupon."""
        is_valid, result = CouponService.validate_coupon(
            code='SAVE20',
            user=customer_user,
            cart_total=Decimal('100.00')
        )
        
        assert is_valid is True
        assert result == active_coupon
    
    def test_validate_invalid_code(self, customer_user):
        """Test validating invalid coupon code."""
        is_valid, error = CouponService.validate_coupon(
            code='INVALID',
            user=customer_user,
        )
        
        assert is_valid is False
        assert 'Invalid' in error
    
    def test_validate_below_minimum(self, active_coupon, customer_user):
        """Test validating with cart below minimum."""
        is_valid, error = CouponService.validate_coupon(
            code='SAVE20',
            user=customer_user,
            cart_total=Decimal('30.00')
        )
        
        assert is_valid is False
        assert 'Minimum' in error
    
    def test_calculate_percentage_discount(self, active_coupon):
        """Test calculating percentage discount."""
        discount = CouponService.calculate_discount(
            coupon=active_coupon,
            subtotal=Decimal('100.00')
        )
        
        assert discount == Decimal('20.00')
    
    def test_calculate_fixed_discount(self, admin_user):
        """Test calculating fixed discount."""
        coupon = Coupon.objects.create(
            code='FIXED10',
            discount_type='fixed',
            discount_value=Decimal('10'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            created_by=admin_user,
        )
        
        discount = CouponService.calculate_discount(
            coupon=coupon,
            subtotal=Decimal('100.00')
        )
        
        assert discount == Decimal('10.00')
    
    def test_max_discount_cap(self, admin_user):
        """Test max discount cap is applied."""
        coupon = Coupon.objects.create(
            code='CAPPED',
            discount_type='percentage',
            discount_value=Decimal('50'),
            max_discount_amount=Decimal('25'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            created_by=admin_user,
        )
        
        discount = CouponService.calculate_discount(
            coupon=coupon,
            subtotal=Decimal('100.00')
        )
        
        # 50% of 100 = 50, but max is 25
        assert discount == Decimal('25.00')


@pytest.mark.django_db
class TestCouponValidateView:
    """Tests for coupon validation endpoint."""
    
    def test_validate_coupon(self, api_client, customer_user, active_coupon):
        """Test validating coupon via API."""
        api_client.force_authenticate(user=customer_user)

        response = api_client.post('/api/promotions/validate/', {
            'code': 'SAVE20',
            'cart_total': '100.00',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'SAVE20'
        assert response.data['discount_type'] == 'percentage'
        assert Decimal(response.data['estimated_discount']) == Decimal('20.00')
    
    def test_validate_invalid_coupon(self, api_client, customer_user):
        """Test validating invalid coupon."""
        api_client.force_authenticate(user=customer_user)
        
        response = api_client.post('/api/promotions/validate/', {
            'code': 'INVALID',
            'cart_total': '100.00',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data
class TestAdminCouponViews:
    """Tests for admin coupon endpoints."""
    
    def test_create_coupon(self, api_client, admin_user):
        """Test admin can create coupon."""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.post('/api/promotions/admin/', {
            'code': 'NEWCODE',
            'discount_type': 'percentage',
            'discount_value': '15',
            'start_date': (timezone.now()).isoformat(),
            'end_date': (timezone.now() + timedelta(days=30)).isoformat(),
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'NEWCODE'
    
    def test_list_coupons(self, api_client, admin_user, active_coupon):
        """Test admin can list all coupons."""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get('/api/promotions/admin/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestSellerCouponViews:
    """Tests for seller coupon endpoints."""
    
    def test_create_seller_coupon(self, api_client, seller_user):
        """Test seller can create coupon for their products."""
        api_client.force_authenticate(user=seller_user)
        
        response = api_client.post('/api/promotions/seller/', {
            'code': 'SELLERCODE',
            'discount_type': 'percentage',
            'discount_value': '10',
            'start_date': (timezone.now()).isoformat(),
            'end_date': (timezone.now() + timedelta(days=7)).isoformat(),
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify scope is set to seller
        coupon = Coupon.objects.get(code='SELLERCODE')
        assert coupon.scope == 'seller'
        assert coupon.seller == seller_user.seller_profile
