"""
Fixtures partagées pour tous les tests API
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import SellerProfile
from apps.catalog.models import Category, ProductType, Product
from apps.customers.models import CustomerProfile
from decimal import Decimal
import uuid

User = get_user_model()


def create_user(username, email, password='test123456', role='customer'):
    """Crée un utilisateur test"""
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role
    )
    # Set is_staff for admin users
    if role == 'admin':
        user.is_staff = True
        user.is_superuser = True
        user.save()
    return user


def create_seller(username='seller1', email='seller1@test.com', shop_name=None):
    """Crée un utilisateur vendeur avec profil"""
    if shop_name is None:
        shop_name = f'Test Shop {uuid.uuid4().hex[:8]}'
    
    user = create_user(username, email, role='seller')
    seller = SellerProfile.objects.create(
        user=user,
        shop_name=shop_name,
        shop_description='Test seller',
        business_type='individual',
        country='France',
        approval_status='approved'
    )
    return user, seller


def create_customer(username='customer1', email='customer1@test.com'):
    """Crée un client avec profil"""
    user = create_user(username, email, role='customer')
    profile = CustomerProfile.objects.create(user=user)
    return user, profile


def create_admin(username='admin', email='admin@test.com'):
    """Crée un admin"""
    return create_user(username, email, role='admin')


def get_auth_token(user):
    """Récupère le token JWT pour un utilisateur"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def get_auth_headers(user):
    """Retourne les headers d'auth pour un user"""
    token = get_auth_token(user)
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


def create_category(name='Test Category'):
    """Crée une catégorie de produit"""
    category, _ = Category.objects.get_or_create(
        name=name,
        defaults={'slug': name.lower().replace(' ', '-')}
    )
    return category


def create_product_type(name='Test Type'):
    """Crée un type de produit"""
    product_type, _ = ProductType.objects.get_or_create(
        name=name,
        defaults={'is_active': True}
    )
    return product_type


def create_product(seller, name='Test Product', price='100.00', quantity=10):
    """Crée un produit"""
    category = create_category()
    product_type = create_product_type()
    
    product = Product.objects.create(
        seller=seller,
        name=name,
        slug=name.lower().replace(' ', '-'),
        description='Test product',
        category=category,
        product_type=product_type,
        price=Decimal(price),
        stock=quantity,
        status='published'
    )
    return product


# Advanced test utilities

class AuthenticatedAPIClient(APIClient):
    """APIClient convenievnce wrapper with auth methods"""
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.force_authenticate(user=user)
    
    def set_auth(self, user):
        """Authenticate to a user"""
        self.force_authenticate(user=user)
    
    def clear_auth(self):
        """Remove authentication"""
        self.force_authenticate(user=None)

