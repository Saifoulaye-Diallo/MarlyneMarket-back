from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Review, ReviewHelpful
from apps.catalog.models import Product, Category, ProductType
from apps.accounts.models import SellerProfile
from decimal import Decimal

User = get_user_model()


class ReviewModelTest(TestCase):
    """Tests pour le modèle Review"""
    
    def setUp(self):
        # Créer vendeur et produit
        seller_user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            role='seller'
        )
        seller = SellerProfile.objects.create(
            user=seller_user,
            shop_name='Test Shop'
        )
        
        category = Category.objects.create(name='Test', slug='test')
        ptype = ProductType.objects.create(name='Test')
        
        self.product = Product.objects.create(
            seller=seller,
            category=category,
            product_type=ptype,
            name='Test Product',
            description='Test',
            price=Decimal('99.99')
        )
        
        # Créer client
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123',
            role='customer'
        )
        
        # Créer review
        self.review = Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            comment='Great product!',
            is_verified_purchase=True,
            status='pending'
        )
    
    def test_review_creation(self):
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, 'Great product!')
        self.assertTrue(self.review.is_verified_purchase)
        self.assertEqual(self.review.status, 'pending')
    
    def test_review_defaults(self):
        self.assertEqual(self.review.helpful_count, 0)
        self.assertEqual(self.review.unhelpful_count, 0)
        self.assertIsNone(self.review.seller_response)
    
    def test_review_status_choices(self):
        valid_statuses = ['pending', 'approved', 'rejected']
        for status in valid_statuses:
            self.review.status = status
            self.review.save()
            self.review.refresh_from_db()
            self.assertEqual(self.review.status, status)
    
    def test_review_rating_range(self):
        for rating in [1, 2, 3, 4, 5]:
            self.review.rating = rating
            self.review.save()
            self.review.refresh_from_db()
            self.assertEqual(self.review.rating, rating)
    
    def test_seller_response(self):
        response_text = 'Thank you for your review!'
        self.review.seller_response = response_text
        self.review.save()
        
        self.review.refresh_from_db()
        self.assertEqual(self.review.seller_response, response_text)
    
    def test_order_reference(self):
        order_ref = 'ORDER-12345'
        self.review.order_reference = order_ref
        self.review.save()
        
        self.review.refresh_from_db()
        self.assertEqual(self.review.order_reference, order_ref)


class ReviewHelpfulModelTest(TestCase):
    """Tests pour le modèle ReviewHelpful"""
    
    def setUp(self):
        # Setup
        seller_user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            role='seller'
        )
        seller = SellerProfile.objects.create(
            user=seller_user,
            shop_name='Test Shop'
        )
        
        category = Category.objects.create(name='Test', slug='test')
        ptype = ProductType.objects.create(name='Test')
        
        product = Product.objects.create(
            seller=seller,
            category=category,
            product_type=ptype,
            name='Test',
            description='Test',
            price=Decimal('99.99')
        )
        
        customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123'
        )
        
        self.review = Review.objects.create(
            product=product,
            user=customer,
            rating=5,
            comment='Great!'
        )
        
        # Créer votants
        self.voter1 = User.objects.create_user(
            username='voter1',
            email='voter1@example.com',
            password='pass123'
        )
        
        self.helpful_vote = ReviewHelpful.objects.create(
            review=self.review,
            user=self.voter1,
            vote_type='helpful'
        )
    
    def test_helpful_vote_creation(self):
        self.assertEqual(self.helpful_vote.review, self.review)
        self.assertEqual(self.helpful_vote.user, self.voter1)
        self.assertEqual(self.helpful_vote.vote_type, 'helpful')
    
    def test_vote_types(self):
        # Create different voters for each vote type (unique constraint)
        valid_types = ['helpful', 'unhelpful', 'spam']
        for vtype in valid_types:
            voter = User.objects.create_user(
                username=f'voter_{vtype}',
                email=f'voter_{vtype}@example.com',
                password='pass123'
            )
            vote = ReviewHelpful.objects.create(
                review=self.review,
                user=voter,
                vote_type=vtype
            )
            self.assertEqual(vote.vote_type, vtype)
    
    def test_multiple_votes(self):
        voter2 = User.objects.create_user(
            username='voter2',
            email='voter2@example.com',
            password='pass123'
        )
        
        vote2 = ReviewHelpful.objects.create(
            review=self.review,
            user=voter2,
            vote_type='unhelpful'
        )
        
        votes = ReviewHelpful.objects.filter(review=self.review)
        self.assertEqual(votes.count(), 2)
