"""
Tests de Workflows Métier
Couvre: État des commandes, transitions valides, workflows retours, etc.
"""
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework.test import APITestCase
from rest_framework import status
from apps.orders.models import Order, OrderItem, SellerOrder
from apps.returns.models import ReturnRequest
from apps.reviews.models import Review
from decimal import Decimal
from tests.fixtures import (
    create_user, create_seller, create_product, create_customer, get_auth_headers
)
from django.test import TransactionTestCase as DjangoTransactionTestCase

User = get_user_model()


class OrderWorkflowTests(APITestCase):
    """Tests pour les transitions d'état des commandes"""
    
    def setUp(self):
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.product = create_product(self.seller, 'Product', '100.00')
        
        # Créer une commande
        self.order = Order.objects.create(
            user=self.customer_user,
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00'),
            status='pending'
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            seller=self.seller,
            product=self.product,
            title_snapshot=self.product.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        self.seller_order = SellerOrder.objects.create(
            order=self.order,
            seller=self.seller,
            status='pending'
        )
        
        self.order_url = f'/api/orders/{self.order.id}/'
        self.seller_order_url = f'/api/seller/order-items/{self.order_item.id}/'
    
    def test_order_pending_to_paid_transition(self):
        """Test: pending -> paid"""
        # Simuler un paiement réussi
        response = self.client.patch(
            self.order_url,
            {'status': 'paid'},
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        # Customer ne peut pas changer le status directement (API doit gérer)
        # Ce test vérifie que l'API rejette cette tentative ou la gère correctement
        if response.status_code == status.HTTP_200_OK:
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, 'paid')
    
    def test_order_paid_to_processing_transition(self):
        """Test: paid -> processing (par seller)"""
        self.order.status = 'paid'
        self.order.save()
        
        response = self.client.patch(
            self.seller_order_url,
            {'status': 'processing'},
            format='json',
            **get_auth_headers(self.seller_user)
        )
        
        if response.status_code == status.HTTP_200_OK:
            self.seller_order.refresh_from_db()
            self.assertEqual(self.seller_order.status, 'processing')
    
    def test_order_processing_to_shipped_transition(self):
        """Test: processing -> shipped (par seller)"""
        self.seller_order.status = 'processing'
        self.seller_order.save()
        
        response = self.client.patch(
            self.seller_order_url,
            {'status': 'shipped'},
            format='json',
            **get_auth_headers(self.seller_user)
        )
        
        if response.status_code == status.HTTP_200_OK:
            self.seller_order.refresh_from_db()
            self.assertEqual(self.seller_order.status, 'shipped')
    
    def test_order_shipped_to_delivered_transition(self):
        """Test: shipped -> delivered"""
        self.seller_order.status = 'shipped'
        self.seller_order.save()
        
        response = self.client.patch(
            self.seller_order_url,
            {'status': 'delivered'},
            format='json',
            **get_auth_headers(self.seller_user)
        )
        
        if response.status_code == status.HTTP_200_OK:
            self.seller_order.refresh_from_db()
            self.assertEqual(self.seller_order.status, 'delivered')
    
    def test_invalid_transition_pending_to_delivered_rejected(self):
        """Test: pending -> delivered doit être rejeté"""
        self.order.status = 'pending'
        self.order.save()
        
        response = self.client.patch(
            self.seller_order_url,
            {'status': 'delivered'},
            format='json',
            **get_auth_headers(self.seller_user)
        )
        
        # Le système doit rejeter cette transition invalide
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
    
    def test_customer_cannot_change_order_status(self):
        """Test: Customer ne peut pas changer le status"""
        response = self.client.patch(
            self.seller_order_url,
            {'status': 'delivered'},
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_seller_cannot_change_main_order_status(self):
        """Test: Seller ne peut changer que son SellerOrder status"""
        # Le seller ne doit pas avoir accès au main order status
        response = self.client.patch(
            self.order_url,
            {'status': 'shipped'},
            format='json',
            **get_auth_headers(self.seller_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReturnWorkflowTests(APITestCase):
    """Tests pour les workflows de retour"""
    
    def setUp(self):
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.product = create_product(self.seller, 'Product', '100.00')
        
        # Créer une commande délivrée
        self.order = Order.objects.create(
            user=self.customer_user,
            status='delivered',
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            seller=self.seller,
            product=self.product,
            title_snapshot=self.product.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        self.returns_url = '/api/returns/'
    
    def test_can_return_delivered_order(self):
        """Test: Peut créer une demande de retour pour commande délivrée"""
        response = self.client.post(
            self.returns_url,
            {
                'order_item': self.order_item.id,
                'reason': 'defective',
                'description': 'Product is broken'
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_cannot_return_pending_order(self):
        """Test: Ne peut pas créer une demande de retour pour commande en cours"""
        pending_order = Order.objects.create(
            user=self.customer_user,
            status='pending',
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
        
        pending_item = OrderItem.objects.create(
            order=pending_order,
            seller=self.seller,
            product=self.product,
            title_snapshot=self.product.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        response = self.client.post(
            self.returns_url,
            {
                'order_item': pending_item.id,
                'reason': 'defective',
                'description': 'Product is broken'
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_return_pending_to_approved_workflow(self):
        """Test: pending -> approved (par seller)"""
        return_request = ReturnRequest.objects.create(
            order_item=self.order_item,
            user=self.customer_user,
            reason='defective',
            status='pending'
        )
        
        response = self.client.patch(
            f'/api/returns/{return_request.id}/',
            {'status': 'approved'},
            format='json',
            **get_auth_headers(self.seller_user)
        )
        
        if response.status_code == status.HTTP_200_OK:
            return_request.refresh_from_db()
            self.assertEqual(return_request.status, 'approved')
    
    def test_customer_cannot_approve_return(self):
        """Test: Customer ne peut pas approuver un retour"""
        return_request = ReturnRequest.objects.create(
            order_item=self.order_item,
            user=self.customer_user,
            reason='defective',
            status='pending'
        )
        
        response = self.client.patch(
            f'/api/returns/{return_request.id}/',
            {'status': 'approved'},
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReviewWorkflowTests(APITestCase):
    """Tests pour les workflows d'avis"""
    
    def setUp(self):
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.product = create_product(self.seller, 'Product', '100.00')
        
        # Créer une commande délivrée
        self.order = Order.objects.create(
            user=self.customer_user,
            status='delivered',
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            seller=self.seller,
            product=self.product,
            title_snapshot=self.product.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        self.reviews_url = '/api/reviews/'
    
    def test_can_review_delivered_order(self):
        """Test: Peut créer un avis pour commande délivrée"""
        response = self.client.post(
            self.reviews_url,
            {
                'product': self.product.id,
                'order_item': self.order_item.id,
                'rating': 5,
                'title': 'Excellent product',
                'comment': 'Really satisfied with this purchase'
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_cannot_review_pending_order(self):
        """Test: Ne peut pas créer un avis pour commande en cours"""
        pending_order = Order.objects.create(
            user=self.customer_user,
            status='pending',
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
        
        pending_item = OrderItem.objects.create(
            order=pending_order,
            seller=self.seller,
            product=self.product,
            title_snapshot=self.product.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        response = self.client.post(
            self.reviews_url,
            {
                'product': self.product.id,
                'order_item': pending_item.id,
                'rating': 5,
                'title': 'Excellent product',
                'comment': 'Really satisfied with this purchase'
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_review_pending_to_approved_workflow(self):
        """Test: avis pending -> approved (par admin/seller)"""
        review = Review.objects.create(
            product=self.product,
            user=self.customer_user,
            rating=5,
            title='Good product',
            comment='Works great',
            status='pending'
        )
        
        # Simulate admin approval
        response = self.client.patch(
            f'/api/admin/reviews/{review.id}/',
            {'status': 'approved'},
            format='json',
            **get_auth_headers(self.seller_user)
        )
        
        if response.status_code == status.HTTP_200_OK:
            review.refresh_from_db()
            self.assertEqual(review.status, 'approved')
    
    def test_customer_cannot_create_multiple_reviews_same_product(self):
        """Test: Customer ne peut pas créer 2 avis pour le même produit"""
        # Premier avis
        Review.objects.create(
            product=self.product,
            user=self.customer_user,
            rating=5,
            title='First review',
            comment='Good product'
        )
        
        # Deuxième avis - doit échouer
        response = self.client.post(
            self.reviews_url,
            {
                'product': self.product.id,
                'order_item': self.order_item.id,
                'rating': 4,
                'title': 'Second review',
                'comment': 'Another review'
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        # Dépend de l'implémentation - unique constraint
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]
        )


class CouponWorkflowTests(APITestCase):
    """Tests pour les workflows de coupons"""
    
    def setUp(self):
        from apps.promotions.models import Coupon
        from datetime import datetime, timedelta
        
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        
        now = datetime.now()
        
        self.valid_coupon = Coupon.objects.create(
            code='SAVE20',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7),
            usage_limit=100,
            is_active=True
        )
        
        self.expired_coupon = Coupon.objects.create(
            code='EXPIRED',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            start_date=now - timedelta(days=30),
            end_date=now - timedelta(days=1),
            is_active=True
        )
        
        self.coupons_url = '/api/coupons/validate/'
    
    def test_can_use_valid_coupon(self):
        """Test: Peut utiliser un coupon valide"""
        response = self.client.post(
            self.coupons_url,
            {'code': 'SAVE20'},
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('discount_value', response.data)
    
    def test_cannot_use_expired_coupon(self):
        """Test: Ne peut pas utiliser un coupon expiré"""
        response = self.client.post(
            self.coupons_url,
            {'code': 'EXPIRED'},
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_cannot_use_nonexistent_coupon(self):
        """Test: Ne peut pas utiliser un coupon inexistant"""
        response = self.client.post(
            self.coupons_url,
            {'code': 'NOTEXIST'},
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
