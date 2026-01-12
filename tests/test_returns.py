"""
Tests for the returns app.
"""
import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, SellerProfile
from apps.catalog.models import Category, ProductType, Product
from apps.orders.models import Order, OrderItem
from apps.returns.models import ReturnRequest


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
def seller_user(db):
    """Create a seller user with profile."""
    user = User.objects.create_user(
        username='seller',
        email='seller@test.com',
        password='testpass123',
        role='seller'
    )
    profile = SellerProfile.objects.create(
        user=user,
        shop_name='Test Shop',
        status='active',
        approval_status='approved'
    )
    return user


@pytest.fixture
def delivered_order(db, customer_user, seller_user):
    """Create a delivered order with items."""
    category = Category.objects.create(name='Test Category', slug='test-category')
    product_type = ProductType.objects.create(name='Test Type')
    product = Product.objects.create(
        name='Test Product',
        description='Test description',
        seller=seller_user.seller_profile,
        category=category,
        product_type=product_type,
        price=Decimal('50.00'),
        stock=10,
    )
    
    order = Order.objects.create(
        user=customer_user,
        reference='TEST-RET-001',
        status='delivered',
        payment_status='paid',
        subtotal=Decimal('50.00'),
        total_amount=Decimal('50.00'),
        currency='EUR',
        shipping_address={
            'name': 'Test User',
            'address': '123 Test St',
            'city': 'Paris',
            'country': 'FR',
            'postal_code': '75001',
        },
    )
    
    order_item = OrderItem.objects.create(
        order=order,
        seller=seller_user.seller_profile,
        product=product,
        title_snapshot='Test Product',
        price_snapshot=Decimal('50.00'),
        quantity=1,
        line_total=Decimal('50.00'),
    )
    
    return order, order_item


@pytest.mark.django_db
class TestReturnRequestModel:
    """Tests for ReturnRequest model."""
    
    def test_create_return_request(self, delivered_order, customer_user):
        """Test creating a return request."""
        order, order_item = delivered_order
        
        return_request = ReturnRequest.objects.create(
            order_item=order_item,
            user=customer_user,
            reason='defective',
            description='Product arrived damaged',
        )

        assert return_request.pk is not None
        assert return_request.status == 'initiated'
        assert return_request.order_item == order_item


@pytest.mark.django_db
class TestCustomerReturnViews:
    """Tests for customer return endpoints."""
    
    def test_create_return_request(self, api_client, customer_user, delivered_order):
        """Test customer can create return request."""
        order, order_item = delivered_order
        
        api_client.force_authenticate(user=customer_user)
        response = api_client.post('/api/returns/', {
            'order_item': order_item.pk,
            'reason': 'defective',
            'description': 'Item broken',
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] in ['requested', 'initiated']
    
    def test_list_own_returns(self, api_client, customer_user, delivered_order):
        """Test customer can list their returns."""
        order, order_item = delivered_order
        
        ReturnRequest.objects.create(
            order_item=order_item,
            user=customer_user,
            reason='defective',
        )
        
        api_client.force_authenticate(user=customer_user)
        response = api_client.get('/api/returns/')
        
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            assert len(response.data['results']) == 1
        else:
            assert len(response.data) == 1


@pytest.mark.django_db
class TestSellerReturnViews:
    """Tests for seller return endpoints."""
    
    def test_list_seller_returns(self, api_client, seller_user, customer_user, delivered_order):
        """Test seller can list returns for their products."""
        order, order_item = delivered_order
        
        ReturnRequest.objects.create(
            order_item=order_item,
            user=customer_user,
            reason='defective',
        )
        
        api_client.force_authenticate(user=seller_user)
        response = api_client.get('/api/returns/seller/')
        
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            assert len(response.data['results']) == 1
        else:
            assert len(response.data) == 1
    
    def test_approve_return(self, api_client, seller_user, customer_user, delivered_order):
        """Test seller can approve return request."""
        order, order_item = delivered_order
        
        return_request = ReturnRequest.objects.create(
            order_item=order_item,
            user=customer_user,
            reason='defective',
        )
        
        api_client.force_authenticate(user=seller_user)
        response = api_client.post(f'/api/returns/seller/{return_request.pk}/approve/')
        
        assert response.status_code == status.HTTP_200_OK
        
        return_request.refresh_from_db()
        assert return_request.status == 'approved'
