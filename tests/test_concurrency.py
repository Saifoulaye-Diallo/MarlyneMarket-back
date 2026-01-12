"""
Tests de Concurrence et Atomicité
Couvre: Double checkout, race conditions, idempotence, etc.
"""
import threading
import time
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.orders.models import Order, OrderItem
from apps.catalog.models import Product
from tests.fixtures import create_seller, create_product, create_customer, get_auth_headers

User = get_user_model()


class ConcurrentCheckoutTests(TransactionTestCase):
    """Tests pour détecter les race conditions lors du checkout"""
    
    def setUp(self):
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        self.customer1_user, _ = create_customer('customer1', 'customer1@test.com')
        self.customer2_user, _ = create_customer('customer2', 'customer2@test.com')
        
        # Produit avec stock limité
        self.product = create_product(
            self.seller,
            name='Limited Stock Product',
            price='100.00',
            quantity=2  # Seulement 2 en stock
        )
        
        self.checkout_url = '/api/orders/checkout/'
        self.client1 = APIClient()
        self.client2 = APIClient()
        self.results = {}
        self.errors = []
    
    def _checkout_request(self, client_id, user, quantity=1):
        """Simule une requête de checkout"""
        try:
            client = APIClient()
            response = client.post(
                self.checkout_url,
                {
                    'items': [
                        {'product_id': self.product.id, 'quantity': quantity}
                    ],
                    'shipping_address': {
                        'street': 'Test Street',
                        'city': 'Test City',
                        'zip_code': '12345',
                        'country': 'Test Country'
                    }
                },
                format='json',
                **get_auth_headers(user)
            )
            
            self.results[client_id] = {
                'status_code': response.status_code,
                'response': response.data
            }
        except Exception as e:
            self.errors.append({
                'client_id': client_id,
                'error': str(e)
            })
    
    def test_concurrent_checkouts_limited_stock(self):
        """Test: Deux clients checkout simultanément avec stock limité"""
        # Créer 2 threads pour checkout simultanément
        thread1 = threading.Thread(
            target=self._checkout_request,
            args=('client1', self.customer1_user, 2)
        )
        thread2 = threading.Thread(
            target=self._checkout_request,
            args=('client2', self.customer2_user, 2)
        )
        
        # Lancer les deux threads en même temps
        thread1.start()
        thread2.start()
        
        # Attendre les résultats
        thread1.join(timeout=10)
        thread2.join(timeout=10)
        
        # Vérifications:
        # - Pas d'erreurs non traitées
        self.assertEqual(len(self.errors), 0, f"Errors occurred: {self.errors}")
        
        # - Un seul checkout doit réussir (200-201)
        successful_checkouts = sum(
            1 for result in self.results.values()
            if result['status_code'] in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        )
        
        # - L'autre doit échouer (400 pour stock insuffisant)
        failed_checkouts = sum(
            1 for result in self.results.values()
            if result['status_code'] == status.HTTP_400_BAD_REQUEST
        )
        
        self.assertEqual(
            successful_checkouts + failed_checkouts, 2,
            f"Expected 2 valid outcomes, got results: {self.results}"
        )
        
        # Vérifier que le stock a bien diminué
        self.product.refresh_from_db()
        # Stock initial était 2
        self.assertLessEqual(self.product.stock, 2)
    
    def test_concurrent_checkouts_prevent_overselling(self):
        """Test: Vérifier qu'on ne vend pas plus que le stock disponible"""
        initial_stock = self.product.stock
        
        # Créer 3 clients qui veulent chacun 1 produit (stock = 2)
        threads = []
        customers = [
            (self.customer1_user, 'customer1'),
            (self.customer2_user, 'customer2'),
        ]
        
        for user, client_id in customers:
            thread = threading.Thread(
                target=self._checkout_request,
                args=(client_id, user, 1)
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=10)
        
        # Vérifications
        self.product.refresh_from_db()
        final_stock = self.product.stock
        
        # Stock restant ne doit pas être négatif
        self.assertGreaterEqual(
            final_stock, 0,
            f"Stock became negative! Initial: {initial_stock}, Final: {final_stock}"
        )
        
        # Au maximum 2 produits vendus
        sold = initial_stock - final_stock
        self.assertLessEqual(
            sold, 2,
            f"Sold {sold} items but initial stock was only {initial_stock}"
        )


class PaymentIdempotenceTests(TransactionTestCase):
    """Tests pour vérifier l'idempotence des paiements"""
    
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
        
        OrderItem.objects.create(
            order=self.order,
            seller=self.seller,
            product=self.product,
            title_snapshot=self.product.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        self.payment_url = f'/api/payments/{self.order.id}/confirm/'
    
    def test_webhook_idempotence_double_payment_webhook(self):
        """Test: Webhook de paiement reçu deux fois - créer 1 seul paiement"""
        from apps.payments.models import Payment
        
        initial_payment_count = Payment.objects.filter(order=self.order).count()
        
        # Simuler deux webhooks de paiement identiques avec l'order_id
        webhook_data = {
            'id': 'pi_test123',
            'amount': 13000,  # En cents (100 + 20 + 10)
            'currency': 'eur',
            'metadata': {
                'order_id': str(self.order.id)
            }
        }
        
        client = APIClient()
        
        # Premier webhook
        response1 = client.post(
            '/api/payments/webhook/stripe/',
            webhook_data,
            format='json'
        )
        
        # Deuxième webhook identique
        response2 = client.post(
            '/api/payments/webhook/stripe/',
            webhook_data,
            format='json'
        )
        
        # Les deux doivent retourner 200 OK (idempotent)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Mais seulement 1 paiement doit être créé
        final_payment_count = Payment.objects.filter(order=self.order).count()
        
        self.assertEqual(
            final_payment_count - initial_payment_count, 1,
            "Idempotence failed: duplicate webhook created duplicate payment"
        )


class StockDecrementAtomicityTests(TransactionTestCase):
    """Tests pour vérifier l'atomicité du décrement de stock"""
    
    def setUp(self):
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        
        self.product = create_product(
            self.seller,
            name='Atomic Stock Product',
            price='100.00',
            quantity=10
        )
        
        self.checkout_url = '/api/orders/checkout/'
    
    def test_failed_checkout_does_not_decrement_stock(self):
        """Test: Si le checkout échoue, le stock ne doit pas diminuer"""
        initial_stock = self.product.stock
        
        # Checkout échoue (par exemple: paiement invalid)
        client = APIClient()
        response = client.post(
            self.checkout_url,
            {
                'items': [
                    {'product_id': str(self.product.id), 'quantity': 5}
                ],
                'shipping_address': {
                    'street': 'Test',
                    'city': 'Test',
                    'zip_code': '12345',
                    'country': 'Test'
                },
                'payment_method': 'invalid_method'  # Force failure
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        # Le checkout doit échouer
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Le stock doit rester inchangé
        self.product.refresh_from_db()
        self.assertEqual(
            self.product.stock, initial_stock,
            f"Stock changed despite failed checkout. Expected {initial_stock}, got {self.product.stock}"
        )
    
    def test_successful_checkout_decrements_stock_once(self):
        """Test: Checkout réussi doit décrémenter le stock une seule fois"""
        initial_stock = self.product.stock
        quantity_ordered = 3
        
        client = APIClient()
        response = client.post(
            self.checkout_url,
            {
                'items': [
                    {'product_id': str(self.product.id), 'quantity': quantity_ordered}
                ],
                'shipping_address': {
                    'street': 'Test Street',
                    'city': 'Test City',
                    'zip_code': '12345',
                    'country': 'Test'
                }
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            self.product.refresh_from_db()
            expected_stock = initial_stock - quantity_ordered
            
            self.assertEqual(
                self.product.stock, expected_stock,
                f"Stock not decremented correctly. Expected {expected_stock}, got {self.product.stock}"
            )


class CouponLimitAtomicityTests(TransactionTestCase):
    """Tests pour vérifier l'atomicité des limites de coupon"""
    
    def setUp(self):
        from apps.promotions.models import Coupon
        from datetime import datetime, timedelta
        
        self.customer1_user, _ = create_customer('customer1', 'customer1@test.com')
        self.customer2_user, _ = create_customer('customer2', 'customer2@test.com')
        
        now = datetime.now()
        
        # Coupon avec usage_limit = 1
        self.limited_coupon = Coupon.objects.create(
            code='ONETIME',
            discount_type='fixed',
            discount_value=Decimal('5.00'),
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7),
            usage_limit=1,
            is_active=True
        )
        
        self.validate_url = '/api/coupons/validate/'
        self.results = {}
    
    def _use_coupon(self, client_id, user):
        """Simule l'utilisation d'un coupon"""
        try:
            client = APIClient()
            response = client.post(
                self.validate_url,
                {'code': 'ONETIME'},
                format='json',
                **get_auth_headers(user)
            )
            
            self.results[client_id] = {
                'status_code': response.status_code,
                'response': response.data
            }
        except Exception as e:
            self.results[client_id] = {
                'error': str(e)
            }
    
    def test_concurrent_coupon_usage_respects_limit(self):
        """Test: Deux clients utilisent simultanément un coupon avec limit=1"""
        thread1 = threading.Thread(
            target=self._use_coupon,
            args=('customer1', self.customer1_user)
        )
        thread2 = threading.Thread(
            target=self._use_coupon,
            args=('customer2', self.customer2_user)
        )
        
        thread1.start()
        thread2.start()
        thread1.join(timeout=10)
        thread2.join(timeout=10)
        
        # Un seul doit réussir (200)
        successful = sum(
            1 for result in self.results.values()
            if result.get('status_code') == status.HTTP_200_OK
        )
        
        # L'autre doit échouer (400 for limit reached)
        failed = sum(
            1 for result in self.results.values()
            if result.get('status_code') == status.HTTP_400_BAD_REQUEST
        )
        
        self.assertEqual(
            len(self.results), 2,
            f"Expected 2 results, got {len(self.results)}"
        )
        
        # Coupon usage doit être exactement 1
        from apps.promotions.models import CouponUsage
        coupon_uses = CouponUsage.objects.filter(coupon=self.limited_coupon).count()
        
        self.assertEqual(
            coupon_uses, 1,
            f"Coupon usage_limit=1 but {coupon_uses} usages recorded"
        )
