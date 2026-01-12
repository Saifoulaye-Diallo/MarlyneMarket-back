"""
Tests de Permissions et RBAC
Couvre: seller A ne voit pas products seller B, customer ne voit pas endpoints seller, etc.
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.catalog.models import Product
from apps.orders.models import Order, OrderItem, SellerOrder
from decimal import Decimal
from tests.fixtures import (
    create_user, create_seller, create_product, create_customer,
    get_auth_headers, create_admin
)

User = get_user_model()


class SellerProductPermissionTests(APITestCase):
    """Tests pour les permissions d'accès aux produits vendeur"""
    
    def setUp(self):
        self.seller1_user, self.seller1 = create_seller('seller1', 'seller1@test.com')
        self.seller2_user, self.seller2 = create_seller('seller2', 'seller2@test.com')
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.admin_user = create_admin('admin', 'admin@test.com')
        
        # Produits
        self.product_seller1 = create_product(
            self.seller1,
            name='Product S1',
            price='100.00'
        )
        self.product_seller2 = create_product(
            self.seller2,
            name='Product S2',
            price='100.00'
        )
        
        self.product_url_s1 = f'/api/products/{self.product_seller1.id}/'
        self.product_url_s2 = f'/api/products/{self.product_seller2.id}/'
        self.products_url = '/api/products/'
    
    def test_seller_can_list_own_products(self):
        """Test qu'un seller voit seulement ses propres produits"""
        response = self.client.get(
            self.products_url,
            **get_auth_headers(self.seller1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_ids = [p['id'] for p in response.data.get('results', response.data)]
        
        # Doit voir son produit
        self.assertIn(self.product_seller1.id, product_ids)
        # Ne doit pas voir le produit de l'autre
        self.assertNotIn(self.product_seller2.id, product_ids)
    
    def test_seller_cannot_update_other_seller_product(self):
        """Test qu'un seller ne peut pas modifier le produit d'un autre"""
        response = self.client.patch(
            self.product_url_s2,
            {'name': 'Hacked Product'},
            format='json',
            **get_auth_headers(self.seller1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Vérifier que le nom n'a pas changé
        self.product_seller2.refresh_from_db()
        self.assertEqual(self.product_seller2.name, 'Product S2')
    
    def test_seller_can_update_own_product(self):
        """Test qu'un seller peut modifier son propre produit"""
        response = self.client.patch(
            self.product_url_s1,
            {'name': 'Updated Product', 'price': '150.00'},
            format='json',
            **get_auth_headers(self.seller1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product_seller1.refresh_from_db()
        self.assertEqual(self.product_seller1.name, 'Updated Product')
    
    def test_seller_cannot_delete_other_seller_product(self):
        """Test qu'un seller ne peut pas supprimer le produit d'un autre"""
        response = self.client.delete(
            self.product_url_s2,
            **get_auth_headers(self.seller1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Vérifier que le produit existe toujours
        self.assertTrue(Product.objects.filter(id=self.product_seller2.id).exists())
    
    def test_seller_can_delete_own_product(self):
        """Test qu'un seller peut supprimer son propre produit"""
        product_id = self.product_seller1.id
        
        response = self.client.delete(
            self.product_url_s1,
            **get_auth_headers(self.seller1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Vérifier que le produit a été supprimé
        self.assertFalse(Product.objects.filter(id=product_id).exists())
    
    def test_customer_cannot_create_product(self):
        """Test qu'un customer ne peut pas créer de produit"""
        response = self.client.post(
            self.products_url,
            {
                'name': 'New Product',
                'price': '100.00',
                'category': 'electronics'
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_update_any_product(self):
        """Test qu'un admin peut modifier n'importe quel produit"""
        response = self.client.patch(
            self.product_url_s1,
            {'name': 'Admin Modified Product'},
            format='json',
            **get_auth_headers(self.admin_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product_seller1.refresh_from_db()
        self.assertEqual(self.product_seller1.name, 'Admin Modified Product')


class SellerOrderPermissionTests(APITestCase):
    """Tests pour les permissions d'accès aux commandes par seller"""
    
    def setUp(self):
        self.seller1_user, self.seller1 = create_seller('seller1', 'seller1@test.com')
        self.seller2_user, self.seller2 = create_seller('seller2', 'seller2@test.com')
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        
        # Produits
        self.product_s1 = create_product(self.seller1, 'Product S1', '100.00')
        self.product_s2 = create_product(self.seller2, 'Product S2', '100.00')
        
        # Commandes
        self.order = Order.objects.create(
            user=self.customer_user,
            subtotal=Decimal('200.00'),
            tax=Decimal('40.00'),
            shipping_fee=Decimal('10.00')
        )
        
        self.item_s1 = OrderItem.objects.create(
            order=self.order,
            seller=self.seller1,
            product=self.product_s1,
            title_snapshot=self.product_s1.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        self.item_s2 = OrderItem.objects.create(
            order=self.order,
            seller=self.seller2,
            product=self.product_s2,
            title_snapshot=self.product_s2.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        # SellerOrders
        self.seller_order_s1 = SellerOrder.objects.create(
            order=self.order,
            seller=self.seller1,
            status='pending'
        )
        
        self.seller_order_s2 = SellerOrder.objects.create(
            order=self.order,
            seller=self.seller2,
            status='pending'
        )
        
        self.seller_orders_url = '/api/seller/orders/'
    
    def test_seller_can_view_own_order_items(self):
        """Test qu'un seller voit seulement ses OrderItems"""
        response = self.client.get(
            self.seller_orders_url,
            **get_auth_headers(self.seller1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Seller1 doit voir son item
        item_ids = [item['id'] for item in response.data.get('results', response.data)]
        self.assertIn(self.item_s1.id, item_ids)
    
    def test_seller_cannot_view_other_seller_items(self):
        """Test qu'un seller ne voit pas les items des autres sellers"""
        response = self.client.get(
            self.seller_orders_url,
            **get_auth_headers(self.seller1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Seller1 ne doit pas voir l'item de seller2
        item_ids = [item['id'] for item in response.data.get('results', response.data)]
        self.assertNotIn(self.item_s2.id, item_ids)
    
    def test_seller_cannot_update_other_seller_order_status(self):
        """Test qu'un seller ne peut pas modifier le status d'un SellerOrder d'un autre"""
        response = self.client.patch(
            f'/api/orders/seller/{self.seller_order_s2.id}/',
            {'status': 'shipped'},
            format='json',
            **get_auth_headers(self.seller1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CustomerAccessPermissionTests(APITestCase):
    """Tests pour vérifier qu'un customer ne peut pas accéder aux endpoints seller"""
    
    def setUp(self):
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
    
    def test_customer_cannot_access_seller_products(self):
        """Test qu'un customer ne peut pas accéder /api/seller/products/"""
        response = self.client.get(
            '/api/seller/products/',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_customer_cannot_access_seller_orders(self):
        """Test qu'un customer ne peut pas accéder /api/seller/orders/"""
        response = self.client.get(
            '/api/seller/orders/',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_customer_cannot_access_seller_analytics(self):
        """Test qu'un customer ne peut pas accéder /api/seller/analytics/"""
        response = self.client.get(
            '/api/seller/analytics/',
            **get_auth_headers(self.customer_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_seller_cannot_access_admin_endpoints(self):
        """Test qu'un seller ne peut pas accéder les endpoints admin"""
        response = self.client.get(
            '/api/admin/users/',
            **get_auth_headers(self.seller_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminAccessTests(APITestCase):
    """Tests pour vérifier que l'admin peut tout accéder"""
    
    def setUp(self):
        self.admin_user = create_admin('admin', 'admin@test.com')
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        self.product = create_product(self.seller, 'Product', '100.00')
    
    def test_admin_can_view_all_products(self):
        """Test que l'admin voit tous les produits"""
        response = self.client.get(
            '/api/admin/products/',
            **get_auth_headers(self.admin_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_can_view_all_sellers(self):
        """Test que l'admin voit tous les sellers"""
        response = self.client.get(
            '/api/admin/sellers/',
            **get_auth_headers(self.admin_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_can_view_all_users(self):
        """Test que l'admin voit tous les utilisateurs"""
        response = self.client.get(
            '/api/admin/users/',
            **get_auth_headers(self.admin_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
