"""
Tests API pour les commandes (Orders)
Couvre: checkout multi-seller, stock insuffisant, produit inactif, seller suspendu
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from apps.orders.models import Order, OrderItem
from apps.catalog.models import Product
from apps.accounts.models import SellerProfile
from tests.fixtures import (
    create_user, create_seller, create_product, create_customer,
    get_auth_headers, AuthenticatedAPIClient
)

User = get_user_model()


class OrderCheckoutTests(APITestCase):
    """Tests pour le checkout et création de commandes"""
    
    def setUp(self):
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.seller1_user, self.seller1 = create_seller('seller1', 'seller1@test.com')
        self.seller2_user, self.seller2 = create_seller('seller2', 'seller2@test.com')
        
        # Créer des produits
        self.product1 = create_product(
            self.seller1,
            name='iPhone 15',
            price='999.99',
            quantity=10
        )
        self.product2 = create_product(
            self.seller2,
            name='Samsung S24',
            price='899.99',
            quantity=10
        )
        
        self.checkout_url = '/api/orders/checkout/'
        self.orders_url = '/api/orders/'
    
    def test_checkout_multi_seller_success(self):
        """Test checkout avec produits de 2 sellers différents"""

        # Force seller approval
        self.product1.seller.approval_status = 'approved'
        self.product1.seller.save()
        self.product2.seller.approval_status = 'approved'
        self.product2.seller.save()

        response = self.client.post(
            self.checkout_url,
            {
                'items': [
                    {
                        'product_id': self.product1.id,
                        'quantity': 1
                    },
                    {
                        'product_id': self.product2.id,
                        'quantity': 2
                    }
                ],
                'shipping_address': {
                    'full_name': 'John Doe',
                    'address1': '123 Main St',
                    'city': 'Paris',
                    'postal_code': '75001',
                    'country': 'France'
                }
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        
        # Vérifier que la commande a été créée avec les bons items
        order = Order.objects.get(id=response.data['id'])
        self.assertEqual(order.user, self.customer_user)
        self.assertEqual(order.items.count(), 2)
        
        # Vérifier les items
        items = order.items.all()
        self.assertEqual(items[0].product, self.product1)
        self.assertEqual(items[0].quantity, 1)
        self.assertEqual(items[1].product, self.product2)
        self.assertEqual(items[1].quantity, 2)
    
    def test_checkout_insufficient_stock(self):
        """Test checkout avec stock insuffisant"""
        response = self.client.post(
            self.checkout_url,
            {
                'items': [
                    {
                        'product_id': self.product1.id,
                        'quantity': 100  # Stock insuffisant
                    }
                ],
                'shipping_address': {
                    'full_name': 'John Doe',
                    'street_address': '123 Main St',
                    'city': 'Paris',
                    'postal_code': '75001',
                    'country': 'France'
                }
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('stock', str(response.data).lower())
    
    def test_checkout_inactive_product(self):
        """Test checkout avec produit inactif"""
        self.product1.status = 'draft'  # Change status to non-published
        self.product1.save()
        
        response = self.client.post(
            self.checkout_url,
            {
                'items': [
                    {
                        'product_id': self.product1.id,
                        'quantity': 1
                    }
                ],
                'shipping_address': {
                    'full_name': 'John Doe',
                    'street_address': '123 Main St',
                    'city': 'Paris',
                    'postal_code': '75001',
                    'country': 'France'
                }
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_checkout_suspended_seller(self):
        """Test checkout avec vendeur suspendu"""
        self.seller1.approval_status = 'suspended'
        self.seller1.save()
        
        response = self.client.post(
            self.checkout_url,
            {
                'items': [
                    {
                        'product_id': self.product1.id,
                        'quantity': 1
                    }
                ],
                'shipping_address': {
                    'full_name': 'John Doe',
                    'street_address': '123 Main St',
                    'city': 'Paris',
                    'postal_code': '75001',
                    'country': 'France'
                }
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_checkout_stock_decremented(self):
        """Test que le stock est décrémenté après checkout"""
        initial_stock = self.product1.stock
        

        # Force seller approval
        self.product1.seller.approval_status = 'approved'
        self.product1.seller.save()

        self.client.post(
            self.checkout_url,
            {
                'items': [
                    {
                        'product_id': self.product1.id,
                        'quantity': 3
                    }
                ],
                'shipping_address': {
                    'full_name': 'John Doe',
                    'address1': '123 Main St',
                    'city': 'Paris',
                    'postal_code': '75001',
                    'country': 'France'
                }
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, initial_stock - 3)
    
    def test_checkout_empty_items(self):
        """Test checkout avec panier vide"""
        response = self.client.post(
            self.checkout_url,
            {
                'items': [],
                'shipping_address': {
                    'full_name': 'John Doe',
                    'street_address': '123 Main St',
                    'city': 'Paris',
                    'postal_code': '75001',
                    'country': 'France'
                }
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_checkout_invalid_product_id(self):
        """Test checkout avec product_id invalide"""
        response = self.client.post(
            self.checkout_url,
            {
                'items': [
                    {
                        'product_id': 'invalid-uuid',
                        'quantity': 1
                    }
                ],
                'shipping_address': {
                    'full_name': 'John Doe',
                    'street_address': '123 Main St',
                    'city': 'Paris',
                    'postal_code': '75001',
                    'country': 'France'
                }
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_checkout_unauthenticated(self):
        """Test checkout sans authentification"""
        response = self.client.post(
            self.checkout_url,
            {
                'items': [
                    {
                        'product_id': self.product1.id,
                        'quantity': 1
                    }
                ],
                'shipping_address': {
                    'full_name': 'John Doe',
                    'street_address': '123 Main St',
                    'city': 'Paris',
                    'postal_code': '75001',
                    'country': 'France'
                }
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderListingTests(APITestCase):
    """Tests pour la liste des commandes"""
    
    def setUp(self):
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.other_customer_user, _ = create_customer('customer2', 'customer2@test.com')
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        
        # Créer des commandes
        self.product = create_product(self.seller, 'Test', '100.00')
        
        self.order1 = Order.objects.create(
            user=self.customer_user,
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
        OrderItem.objects.create(
            order=self.order1,
            seller=self.seller,
            product=self.product,
            title_snapshot=self.product.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        self.order2 = Order.objects.create(
            user=self.other_customer_user,
            subtotal=Decimal('200.00'),
            tax=Decimal('40.00'),
            shipping_fee=Decimal('10.00')
        )
        
        self.orders_url = '/api/orders/'
    
    def test_customer_can_list_own_orders(self):
        """Test qu'un client voit seulement ses propres commandes"""
        response = self.client.get(
            self.orders_url,
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated or direct list response
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Vérifier qu'il ne voit que sa commande
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.order1.id)
    
    def test_customer_cannot_see_other_orders(self):
        """Test qu'un client ne voit pas les commandes d'un autre"""
        response = self.client.get(
            self.orders_url,
            **get_auth_headers(self.customer_user)
        )
        
        # Handle paginated or direct list response
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        order_ids = [order['id'] for order in data]
        self.assertNotIn(self.order2.id, order_ids)
    
    def test_unauthenticated_cannot_list_orders(self):
        """Test qu'on ne peut pas lister les commandes sans auth"""
        response = self.client.get(self.orders_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderDetailTests(APITestCase):
    """Tests pour les détails d'une commande"""
    
    def setUp(self):
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.other_customer_user, _ = create_customer('customer2', 'customer2@test.com')
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        
        self.product = create_product(self.seller, 'Test', '100.00')
        
        self.order = Order.objects.create(
            user=self.customer_user,
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
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
    
    def test_customer_can_view_own_order(self):
        """Test qu'un client peut voir les détails de sa commande"""
        response = self.client.get(
            f'/api/orders/{self.order.id}/',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order.id)
    
    def test_customer_cannot_view_other_order(self):
        """Test qu'un client ne peut pas voir une commande d'un autre"""
        response = self.client.get(
            f'/api/orders/{self.order.id}/',
            **get_auth_headers(self.other_customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unauthenticated_cannot_view_order(self):
        """Test qu'on ne peut pas voir les détails sans auth"""
        response = self.client.get(f'/api/orders/{self.order.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

