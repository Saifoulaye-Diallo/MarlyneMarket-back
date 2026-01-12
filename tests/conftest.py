"""
Pytest configuration and fixtures for marketplace backend tests.

Provides reusable fixtures for:
- Users (super admin, sellers with different statuses)
- JWT tokens for authentication
- Catalog entities (categories, types, attributes, options, rules)
- Product samples (draft, published, with/without attributes)
- API clients (authenticated/unauthenticated)
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import SellerProfile
from apps.catalog.models import (
    Category, ProductType, Attribute, AttributeOption,
    TypeAttributeRule, Product, ProductImage, ProductAttributeValue
)

User = get_user_model()

# Use pytest-django database fixture
pytest_plugins = ['pytest_django']


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def super_admin(db):
    """Create a super admin user."""
    user = User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='testpass123',
        role='super_admin'
    )
    return user


@pytest.fixture
def seller_user(db):
    """Create a seller user."""
    user = User.objects.create_user(
        username='seller1',
        email='seller@test.com',
        password='testpass123',
        role='seller',
        first_name='John',
        last_name='Seller'
    )
    profile = SellerProfile.objects.create(
        user=user,
        shop_name='Test Shop',
        phone='1234567890',
        address='123 Main St',
        city='Test City',
        country='Test Country',
        status='active'
    )
    return user


@pytest.fixture
def seller_user_2(db):
    """Create another seller user."""
    user = User.objects.create_user(
        username='seller2',
        email='seller2@test.com',
        password='testpass123',
        role='seller',
        first_name='Jane',
        last_name='Seller'
    )
    profile = SellerProfile.objects.create(
        user=user,
        shop_name='Another Shop',
        status='active'
    )
    return user


@pytest.fixture
def category(db):
    """Create a product category."""
    return Category.objects.create(
        name='Electronics',
        slug='electronics',
        is_active=True
    )


@pytest.fixture
def product_type(db):
    """Create a product type with attributes."""
    return ProductType.objects.create(
        name='Laptop',
        is_active=True
    )


@pytest.fixture
def attribute_text(db):
    """Create a text attribute."""
    return Attribute.objects.create(
        name='Brand',
        data_type='text',
        is_active=True
    )


@pytest.fixture
def attribute_number(db):
    """Create a number attribute."""
    return Attribute.objects.create(
        name='RAM (GB)',
        data_type='number',
        is_active=True
    )


@pytest.fixture
def attribute_choice(db):
    """Create a choice attribute with options."""
    attr = Attribute.objects.create(
        name='Operating System',
        data_type='choice',
        is_active=True
    )
    AttributeOption.objects.create(attribute=attr, value='Windows')
    AttributeOption.objects.create(attribute=attr, value='macOS')
    AttributeOption.objects.create(attribute=attr, value='Linux')
    return attr


@pytest.fixture
def type_attribute_rules(db, product_type, attribute_text, attribute_number, attribute_choice):
    """Create type attribute rules."""
    TypeAttributeRule.objects.create(
        product_type=product_type,
        attribute=attribute_text,
        is_required=True,
        display_order=1
    )
    TypeAttributeRule.objects.create(
        product_type=product_type,
        attribute=attribute_number,
        is_required=True,
        display_order=2
    )
    TypeAttributeRule.objects.create(
        product_type=product_type,
        attribute=attribute_choice,
        is_required=False,
        display_order=3
    )


@pytest.fixture
def product(db, seller_user, category, product_type, type_attribute_rules):
    """Create a product."""
    return Product.objects.create(
        seller=seller_user.seller_profile,
        category=category,
        product_type=product_type,
        name='Test Laptop',
        description='A great laptop for work',
        price=999.99,
        stock=10,
        status='draft'
    )


@pytest.fixture
def published_product(db, seller_user, category, product_type, type_attribute_rules, attribute_text, attribute_number):
    """Create a published product with all required attributes."""
    prod = Product.objects.create(
        seller=seller_user.seller_profile,
        category=category,
        product_type=product_type,
        name='Published Laptop',
        description='A published laptop',
        price=1299.99,
        stock=5,
        status='published'
    )
    ProductAttributeValue.objects.create(
        product=prod,
        attribute=attribute_text,
        value_text='Apple'
    )
    ProductAttributeValue.objects.create(
        product=prod,
        attribute=attribute_number,
        value_number=16
    )
    return prod


@pytest.fixture
def get_tokens(db, super_admin):
    """Get JWT tokens for super admin."""
    refresh = RefreshToken.for_user(super_admin)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


@pytest.fixture
def get_seller_tokens(db, seller_user):
    """Get JWT tokens for seller."""
    refresh = RefreshToken.for_user(seller_user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


# ============================================================================
# EXTENDED FIXTURES FOR COMPREHENSIVE TESTING
# ============================================================================

@pytest.fixture
def suspended_seller(db):
    """Create a suspended seller user."""
    user = User.objects.create_user(
        username='suspended@test.com',
        email='suspended@test.com',
        password='testpass123',
        role='seller'
    )
    SellerProfile.objects.create(
        user=user,
        shop_name='Suspended Shop',
        phone='9999999999',
        status='suspended'
    )
    return user


@pytest.fixture
def pending_seller(db):
    """Create a pending seller user."""
    user = User.objects.create_user(
        username='pending@test.com',
        email='pending@test.com',
        password='testpass123',
        role='seller'
    )
    SellerProfile.objects.create(
        user=user,
        shop_name='Pending Shop',
        phone='8888888888',
        status='pending'
    )
    return user


@pytest.fixture
def get_seller_2_tokens(db, seller_user_2):
    """Get JWT tokens for second seller."""
    refresh = RefreshToken.for_user(seller_user_2)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


@pytest.fixture
def category_inactive(db):
    """Create an inactive category."""
    return Category.objects.create(
        name='Discontinued',
        slug='discontinued',
        is_active=False
    )


@pytest.fixture
def product_type_inactive(db):
    """Create an inactive product type."""
    return ProductType.objects.create(
        name='Obsolete Type',
        is_active=False
    )


@pytest.fixture
def attribute_bool(db):
    """Create a boolean attribute."""
    return Attribute.objects.create(
        name='Warranty Included',
        data_type='bool',
        is_active=True
    )


@pytest.fixture
def attribute_inactive(db):
    """Create an inactive attribute."""
    return Attribute.objects.create(
        name='Deprecated',
        data_type='text',
        is_active=False
    )


@pytest.fixture
def product_seller_2(db, seller_user_2, category, product_type):
    """Create a product for seller 2."""
    return Product.objects.create(
        seller=seller_user_2.seller_profile,
        category=category,
        product_type=product_type,
        name='Other Seller Product',
        description='From different seller',
        price=1500.00,
        stock=3,
        status='draft'
    )


@pytest.fixture
def product_with_attributes(db, seller_user, category, product_type, 
                           attribute_text, attribute_number, attribute_choice):
    """Create a product with multiple attributes set."""
    prod = Product.objects.create(
        seller=seller_user.seller_profile,
        category=category,
        product_type=product_type,
        name='Full Featured Product',
        description='Has all attributes',
        price=899.99,
        stock=20,
        status='draft'
    )
    ProductAttributeValue.objects.create(
        product=prod,
        attribute=attribute_text,
        value_text='Premium Brand'
    )
    ProductAttributeValue.objects.create(
        product=prod,
        attribute=attribute_number,
        value_number=32
    )
    option = attribute_choice.options.first()
    ProductAttributeValue.objects.create(
        product=prod,
        attribute=attribute_choice,
        value_option=option
    )
    return prod


@pytest.fixture
def product_image(db, product):
    """Create a product image."""
    return ProductImage.objects.create(
        product=product,
        image='test_images/laptop.jpg',
        is_primary=True
    )


@pytest.fixture
def multiple_products(db, seller_user, category, product_type):
    """Create multiple products for list/filter tests."""
    products = []
    for i in range(5):
        prod = Product.objects.create(
            seller=seller_user.seller_profile,
            category=category,
            product_type=product_type,
            name=f'Product {i+1}',
            description=f'Description {i+1}',
            price=100 * (i + 1),
            stock=10 + i,
            status='draft' if i < 3 else 'published'
        )
        products.append(prod)
    return products


@pytest.fixture
def sample_products_for_isolation(db, seller_user, seller_user_2, category, product_type):
    """Create products for multi-vendor isolation tests."""
    seller1_products = [
        Product.objects.create(
            seller=seller_user.seller_profile,
            category=category,
            product_type=product_type,
            name=f'S1 Product {i}',
            description=f'Seller 1 Product {i}',
            price=100 + i,
            stock=10,
            status='draft'
        )
        for i in range(3)
    ]
    seller2_products = [
        Product.objects.create(
            seller=seller_user_2.seller_profile,
            category=category,
            product_type=product_type,
            name=f'S2 Product {i}',
            description=f'Seller 2 Product {i}',
            price=200 + i,
            stock=5,
            status='draft'
        )
        for i in range(2)
    ]
    return {
        'seller1': seller_user,
        'seller2': seller_user_2,
        'seller1_products': seller1_products,
        'seller2_products': seller2_products
    }


@pytest.fixture
def authenticated_client(api_client, get_seller_tokens):
    """API client with seller credentials."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_seller_tokens["access"]}')
    return api_client


@pytest.fixture
def admin_client(api_client, get_tokens):
    """API client with admin credentials."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_tokens["access"]}')
    return api_client


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

pytest_plugins = ['pytest_django']
