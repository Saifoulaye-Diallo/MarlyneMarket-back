"""
Tests for the reviews app.
"""
import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, SellerProfile
from apps.catalog.models import Category, ProductType, Product
from apps.reviews.models import Review, ReviewHelpful


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
def product(db):
    """Create a product for reviews."""
    seller_user = User.objects.create_user(
        username='seller',
        email='seller@test.com',
        password='testpass123',
        role='seller'
    )
    seller = SellerProfile.objects.create(
        user=seller_user,
        shop_name='Test Shop',
        status='active'
    )
    category = Category.objects.create(name='Test', slug='test')
    product_type = ProductType.objects.create(name='Type')
    
    return Product.objects.create(
        name='Test Product',
        description='Test description',
        seller=seller,
        category=category,
        product_type=product_type,
        price=Decimal('50.00'),
        stock=10,
    )


@pytest.mark.django_db
class TestReviewModel:
    """Tests for Review model."""
    
    def test_create_review(self, product, customer_user):
        """Test creating a review."""
        review = Review.objects.create(
            user=customer_user,
            product=product,
            rating=5,
            title='Great product',
            comment='I love this!',
        )
        
        assert review.pk is not None
        assert review.rating == 5
        assert review.status == 'pending'
        assert review.is_verified_purchase is False
    
    def test_unique_user_product_review(self, product, customer_user):
        """Test user can only have one review per product."""
        Review.objects.create(
            user=customer_user,
            product=product,
            rating=5,
            comment='First review',
        )
        
        with pytest.raises(Exception):
            Review.objects.create(
                user=customer_user,
                product=product,
                rating=3,
                comment='Second review',
            )


@pytest.mark.django_db
class TestPublicReviewViews:
    """Tests for public review endpoints."""
    
    def test_list_approved_reviews_only(self, client, product, customer_user):
        """Test public can only see approved reviews."""
        Review.objects.create(
            user=customer_user,
            product=product,
            rating=5,
            comment='Approved',
            status='approved',
        )
        
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123',
        )
        Review.objects.create(
            user=other_user,
            product=product,
            rating=1,
            comment='Not approved',
            status='pending',
        )
        
        response = client.get(f'/api/reviews/?product={product.pk}')
        
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['comment'] == 'Approved'
        else:
            assert len(response.data) == 1
            assert response.data[0]['comment'] == 'Approved'


@pytest.mark.django_db
class TestCustomerReviewViews:
    """Tests for customer review endpoints."""
    
    def test_create_review(self, api_client, customer_user, product):
        """Test customer can create review."""
        api_client.force_authenticate(user=customer_user)
        
        response = api_client.post('/api/reviews/my/', {
            'product': product.pk,
            'rating': 4,
            'title': 'Good product',
            'comment': 'Works well',
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['rating'] == 4
    
    def test_list_own_reviews(self, api_client, customer_user, product):
        """Test customer can list own reviews."""
        Review.objects.create(
            user=customer_user,
            product=product,
            rating=5,
            comment='My review',
        )
        
        api_client.force_authenticate(user=customer_user)
        response = api_client.get('/api/reviews/my/')
        
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            assert len(response.data['results']) == 1
        else:
            assert len(response.data) == 1


@pytest.mark.django_db
class TestAdminReviewViews:
    """Tests for admin review endpoints."""
    
    def test_approve_review(self, api_client, admin_user, customer_user, product):
        """Test admin can approve review."""
        review = Review.objects.create(
            user=customer_user,
            product=product,
            rating=4,
            comment='Pending',
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/reviews/admin/{review.pk}/approve/')
        
        assert response.status_code == status.HTTP_200_OK
        
        review.refresh_from_db()
        assert review.status == 'approved'
    
    def test_reject_review(self, api_client, admin_user, customer_user, product):
        """Test admin can reject review."""
        review = Review.objects.create(
            user=customer_user,
            product=product,
            rating=1,
            comment='Spam content',
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/reviews/admin/{review.pk}/reject/', {
            'moderation_note': 'Contains spam',
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        review.refresh_from_db()
        assert review.status == 'rejected'
        assert 'spam' in review.moderation_note.lower()
