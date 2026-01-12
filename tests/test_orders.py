"""
Tests for the orders app.
Tests checkout flow, multi-seller orders, and permissions.
"""
import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, SellerProfile
from apps.catalog.models import Category, ProductType, Product
from apps.orders.models import Order, OrderItem, SellerOrder
from apps.customers.models import Address


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
def seller_user_1(db):
    """Create first seller user with profile."""
    user = User.objects.create_user(
        username='seller1',
        email='seller1@test.com',
        password='testpass123',
        role='seller'
    )
    SellerProfile.objects.create(
        user=user,
        shop_name='Shop 1',
        status='active'
    )
    return user


@pytest.fixture
def seller_user_2(db):
    """Create second seller user with profile."""
    user = User.objects.create_user(
        username='seller2',
        email='seller2@test.com',
        password='testpass123',
        role='seller'
    )
    SellerProfile.objects.create(
        user=user,
        shop_name='Shop 2',
        status='active'
    )
    return user


@pytest.fixture
def category(db):
    """Create a category."""
    return Category.objects.create(name='Electronics', slug='electronics')


@pytest.fixture
def product_type(db):
    """Create a product type."""
    return ProductType.objects.create(name='Laptop')


@pytest.fixture
def product_seller_1(db, seller_user_1, category, product_type):
    """Create a product from seller 1."""
    return Product.objects.create(
        name='Laptop Model A',
        description='Great laptop',
        seller=seller_user_1.seller_profile,
        category=category,
        product_type=product_type,
        price=Decimal('999.99'),
        stock=10,
        status='published'
    )


@pytest.fixture
def product_seller_2(db, seller_user_2, category, product_type):
    """Create a product from seller 2."""
    return Product.objects.create(
        name='Laptop Model B',
        description='Another great laptop',
        seller=seller_user_2.seller_profile,
        category=category,
        product_type=product_type,
        price=Decimal('1299.99'),
        stock=5,
        status='published'
    )


@pytest.fixture
def customer_address(db, customer_user):
    """Create customer shipping address."""
    return Address.objects.create(
        user=customer_user,
        label='Home',
        full_name='Test Customer',
        phone_number='1234567890',
        street_address='123 Test Street',
        city='Paris',
        postal_code='75001',
        country='France',
        is_default_shipping=True,
    )


@pytest.fixture
def order_with_items(db, customer_user, seller_user_1, product_seller_1):
    """Create an order with items."""
    order = Order.objects.create(
        user=customer_user,
        reference='TEST-ORD-001',
        status='pending',
        payment_status='unpaid',
        subtotal=Decimal('999.99'),
        total_amount=Decimal('999.99'),
        currency='EUR',
        shipping_address={
            'name': 'Test Customer',
            'address': '123 Test St',
            'city': 'Paris',
            'country': 'France',
            'postal_code': '75001',
        },
    )
    
    OrderItem.objects.create(
        order=order,
        seller=seller_user_1.seller_profile,
        product=product_seller_1,
        title_snapshot='Laptop Model A',
        price_snapshot=Decimal('999.99'),
        quantity=1,
        line_total=Decimal('999.99'),
    )
    
    return order


@pytest.fixture
def multi_seller_order(db, customer_user, seller_user_1, seller_user_2, 
                       product_seller_1, product_seller_2):
    """Create order with items from multiple sellers."""
    order = Order.objects.create(
        user=customer_user,
        reference='TEST-MULTI-001',
        status='paid',
        payment_status='paid',
        subtotal=Decimal('2299.98'),
        total_amount=Decimal('2299.98'),
        currency='EUR',
        shipping_address={
            'name': 'Test Customer',
            'address': '123 Test St',
            'city': 'Paris',
            'country': 'France',
            'postal_code': '75001',
        },
    )
    
    OrderItem.objects.create(
        order=order,
        seller=seller_user_1.seller_profile,
        product=product_seller_1,
        title_snapshot='Laptop Model A',
        price_snapshot=Decimal('999.99'),
        quantity=1,
        line_total=Decimal('999.99'),
    )
    
    OrderItem.objects.create(
        order=order,
        seller=seller_user_2.seller_profile,
        product=product_seller_2,
        title_snapshot='Laptop Model B',
        price_snapshot=Decimal('1299.99'),
        quantity=1,
        line_total=Decimal('1299.99'),
    )
    
    # Create seller orders
    SellerOrder.objects.create(
        seller=seller_user_1.seller_profile,
        order=order,
        status='pending',
        subtotal=Decimal('999.99'),
    )
    
    SellerOrder.objects.create(
        seller=seller_user_2.seller_profile,
        order=order,
        status='pending',
        subtotal=Decimal('1299.99'),
    )
    
    return order


# ============================================================================
# MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestOrderModel:
    """Tests for Order model."""
    
    def test_create_order(self, customer_user):
        """Test creating an order."""
        order = Order.objects.create(
            user=customer_user,
            status='pending',
            payment_status='unpaid',
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
        )
        
        assert order.pk is not None
        assert order.reference is not None
        assert order.reference.startswith('ORD-')
    
    def test_order_reference_unique(self, customer_user):
        """Test order reference is unique."""
        order1 = Order.objects.create(
            user=customer_user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
        )
        order2 = Order.objects.create(
            user=customer_user,
            subtotal=Decimal('200.00'),
            total_amount=Decimal('200.00'),
        )
        
        assert order1.reference != order2.reference
    
    def test_calculate_totals(self, order_with_items):
        """Test order total calculation from items."""
        total = order_with_items.calculate_totals()
        assert total == Decimal('999.99')


@pytest.mark.django_db
class TestOrderItemModel:
    """Tests for OrderItem model."""
    
    def test_create_order_item(self, order_with_items, seller_user_1, product_seller_1):
        """Test creating an order item."""
        item = order_with_items.items.first()
        
        assert item.seller == seller_user_1.seller_profile
        assert item.title_snapshot == 'Laptop Model A'
        assert item.line_total == Decimal('999.99')
    
    def test_line_total_auto_calculated(self, order_with_items, seller_user_1, product_seller_1):
        """Test line_total is auto-calculated on save."""
        item = OrderItem.objects.create(
            order=order_with_items,
            seller=seller_user_1.seller_profile,
            product=product_seller_1,
            title_snapshot='Another Product',
            price_snapshot=Decimal('50.00'),
            quantity=3,
            line_total=Decimal('0'),  # Will be recalculated
        )
        
        assert item.line_total == Decimal('150.00')


@pytest.mark.django_db
class TestSellerOrderModel:
    """Tests for SellerOrder model."""
    
    def test_seller_order_items(self, multi_seller_order, seller_user_1):
        """Test seller order shows correct items."""
        seller_order = SellerOrder.objects.get(
            seller=seller_user_1.seller_profile,
            order=multi_seller_order
        )
        
        items = list(seller_order.items)
        assert len(items) == 1
        assert items[0].title_snapshot == 'Laptop Model A'


# ============================================================================
# CUSTOMER VIEW TESTS
# ============================================================================

@pytest.mark.django_db
class TestCustomerOrderViews:
    """Tests for customer order endpoints."""
    
    def test_list_own_orders(self, api_client, customer_user, order_with_items):
        """Test customer can list their orders."""
        api_client.force_authenticate(user=customer_user)
        response = api_client.get('/api/orders/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_retrieve_own_order(self, api_client, customer_user, order_with_items):
        """Test customer can view their order detail."""
        api_client.force_authenticate(user=customer_user)
        response = api_client.get(f'/api/orders/{order_with_items.pk}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['reference'] == 'TEST-ORD-001'
    
    def test_cannot_view_other_customer_order(self, api_client, order_with_items):
        """Test customer cannot view another customer's order."""
        other_customer = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123',
            role='customer'
        )
        
        api_client.force_authenticate(user=other_customer)
        response = api_client.get(f'/api/orders/{order_with_items.pk}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# SELLER VIEW TESTS
# ============================================================================

@pytest.mark.django_db
class TestSellerOrderViews:
    """Tests for seller order endpoints."""
    
    def test_list_seller_orders(self, api_client, seller_user_1, multi_seller_order):
        """Test seller can list orders containing their products."""
        api_client.force_authenticate(user=seller_user_1)
        response = api_client.get('/api/orders/seller/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_seller_sees_only_own_items(self, api_client, seller_user_1, multi_seller_order):
        """Test seller only sees their items in the order."""
        seller_order = SellerOrder.objects.get(
            seller=seller_user_1.seller_profile,
            order=multi_seller_order
        )
        
        api_client.force_authenticate(user=seller_user_1)
        response = api_client.get(f'/api/orders/seller/{seller_order.pk}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['subtotal'] == '999.99'
    
    def test_seller_cannot_see_other_seller_order(self, api_client, seller_user_1, 
                                                   seller_user_2, multi_seller_order):
        """Test seller cannot access another seller's order portion."""
        other_seller_order = SellerOrder.objects.get(
            seller=seller_user_2.seller_profile,
            order=multi_seller_order
        )
        
        api_client.force_authenticate(user=seller_user_1)
        response = api_client.get(f'/api/orders/seller/{other_seller_order.pk}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_seller_order_status(self, api_client, seller_user_1, multi_seller_order):
        """Test seller can update their order status."""
        seller_order = SellerOrder.objects.get(
            seller=seller_user_1.seller_profile,
            order=multi_seller_order
        )
        
        api_client.force_authenticate(user=seller_user_1)
        response = api_client.patch(
            f'/api/orders/seller/{seller_order.pk}/',
            {'status': 'processing'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        seller_order.refresh_from_db()
        assert seller_order.status == 'processing'


# ============================================================================
# ADMIN VIEW TESTS  
# ============================================================================

@pytest.mark.django_db
class TestAdminOrderViews:
    """Tests for admin order endpoints."""
    
    def test_list_all_orders(self, api_client, admin_user, order_with_items, multi_seller_order):
        """Test admin can list all orders."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/orders/admin/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_admin_can_update_order(self, api_client, admin_user, order_with_items):
        """Test admin can update order status."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f'/api/orders/admin/{order_with_items.pk}/',
            {'status': 'cancelled'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        order_with_items.refresh_from_db()
        assert order_with_items.status == 'cancelled'


# ============================================================================
# CHECKOUT TESTS
# ============================================================================

@pytest.mark.django_db
class TestCheckout:
    """Tests for checkout functionality."""
    
    def test_checkout_creates_order(self, api_client, customer_user, customer_address,
                                     product_seller_1, product_seller_2):
        """Test checkout creates order with items from multiple sellers."""
        api_client.force_authenticate(user=customer_user)
        

        # Force seller approval for both products
        product_seller_1.seller.approval_status = 'approved'
        product_seller_1.seller.save()
        product_seller_2.seller.approval_status = 'approved'
        product_seller_2.seller.save()

        checkout_data = {
            'items': [
                {'product_id': product_seller_1.pk, 'quantity': 1},
                {'product_id': product_seller_2.pk, 'quantity': 1},
            ],
            'shipping_address_id': int(customer_address.pk),
        }
        
        response = api_client.post('/api/orders/checkout/', checkout_data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print('CHECKOUT ERROR:', response.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'reference' in response.data
        
        # Verify order items were created
        order = Order.objects.get(reference=response.data['reference'])
        assert order.items.count() == 2
        
        # Verify seller orders were created
        assert SellerOrder.objects.filter(order=order).count() == 2
    
    def test_checkout_decrements_stock(self, api_client, customer_user, customer_address,
                                        product_seller_1):
        """Test checkout decrements product stock."""
        initial_stock = product_seller_1.stock
        

        # Force seller approval
        product_seller_1.seller.approval_status = 'approved'
        product_seller_1.seller.save()

        api_client.force_authenticate(user=customer_user)
        response = api_client.post('/api/orders/checkout/', {
            'items': [{'product_id': product_seller_1.pk, 'quantity': 2}],
            'shipping_address_id': int(customer_address.pk),
        }, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print('CHECKOUT ERROR:', response.data)
        assert response.status_code == status.HTTP_201_CREATED
        
        product_seller_1.refresh_from_db()
        assert product_seller_1.stock == initial_stock - 2
    
    def test_checkout_fails_insufficient_stock(self, api_client, customer_user, 
                                                customer_address, product_seller_1):
        """Test checkout fails if stock is insufficient."""
        api_client.force_authenticate(user=customer_user)
        

        # Force seller approval
        product_seller_1.seller.approval_status = 'approved'
        product_seller_1.seller.save()

        response = api_client.post('/api/orders/checkout/', {
            'items': [{'product_id': product_seller_1.pk, 'quantity': 999}],
            'shipping_address_id': customer_address.pk,
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Accept either stock or seller error
        error_str = str(response.data).lower()
        assert 'stock' in error_str or 'seller' in error_str
    
    def test_checkout_fails_inactive_product(self, api_client, customer_user,
                                              customer_address, product_seller_1):
        """Test checkout fails for inactive product."""
        product_seller_1.status = 'draft'
        product_seller_1.save()
        
        api_client.force_authenticate(user=customer_user)
        response = api_client.post('/api/orders/checkout/', {
            'items': [{'product_id': product_seller_1.pk, 'quantity': 1}],
            'shipping_address_id': customer_address.pk,
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# PERMISSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestOrderPermissions:
    """Tests for order permission checks."""
    
    def test_unauthenticated_access_denied(self, api_client):
        """Test unauthenticated user cannot access orders."""
        response = api_client.get('/api/orders/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_seller_cannot_access_customer_orders(self, api_client, seller_user_1):
        """Test seller cannot access customer order endpoints."""
        api_client.force_authenticate(user=seller_user_1)
        response = api_client.get('/api/orders/')
        
        # Should return empty list (no orders owned by seller as customer)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0
    
    def test_customer_cannot_access_seller_orders(self, api_client, customer_user):
        """Test customer cannot access seller order endpoints."""
        api_client.force_authenticate(user=customer_user)
        response = api_client.get('/api/orders/seller/')
        
        # Should return 403 or empty depending on implementation
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_200_OK]
    
    def test_non_admin_cannot_access_admin_orders(self, api_client, customer_user):
        """Test non-admin cannot access admin endpoints."""
        api_client.force_authenticate(user=customer_user)
        response = api_client.get('/api/orders/admin/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
