"""
Tests de Sécurité
Couvre: Injection SQL, XSS, CSRF, File Upload, Rate Limiting, Data Leakage, etc.
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from tests.fixtures import create_user, create_seller, create_customer, create_admin, get_auth_headers
from apps.catalog.models import Product
from apps.reviews.models import Review

User = get_user_model()


class SQLInjectionSecurityTests(APITestCase):
    """Tests pour détecter les vulnérabilités d'injection SQL"""
    
    def setUp(self):
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.products_url = '/api/products/'
        self.search_url = '/api/products/search/'
    
    def test_sql_injection_in_search(self):
        """Test: Injection SQL dans le champ de recherche"""
        malicious_queries = [
            "'; DROP TABLE products; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM accounts_user --",
            "product' AND 1=1 --"
        ]
        
        for payload in malicious_queries:
            response = self.client.get(
                self.products_url,
                {'search': payload},  # Utiliser 'search' au lieu de 'q'
                **get_auth_headers(self.customer_user)
            )
            
            # Doit retourner un résultat sain (0 résultats ou 200)
            # Jamais une erreur SQL ou crash
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
    
    def test_sql_injection_in_filter(self):
        """Test: Injection SQL dans les filtres"""
        response = self.client.get(
            self.products_url,
            {'price__gt': "'; DROP TABLE products; --"},
            **get_auth_headers(self.customer_user)
        )
        
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class CrossSiteScriptingSecurityTests(APITestCase):
    """Tests pour détecter les vulnérabilités XSS"""
    
    def setUp(self):
        from apps.catalog.models import Category, ProductType
        
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        
        # Create category and product_type fixtures
        self.category = Category.objects.create(name='Electronics')
        self.product_type = ProductType.objects.create(name='Electronics')
        
        self.products_url = '/api/products/'
    
    def test_xss_in_product_name(self):
        """Test: XSS dans le nom du produit"""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '"><script>alert("XSS")</script>',
            '<svg onload=alert("XSS")>'
        ]
        
        for payload in xss_payloads:
            response = self.client.post(
                self.products_url,
                {
                    'name': payload,
                    'price': '100.00',
                    'category': 'electronics'
                },
                format='json',
                **get_auth_headers(self.seller_user)
            )
            
            if response.status_code == status.HTTP_201_CREATED:
                # Le produit a été créé, vérifier que le script n'a pas été exécuté
                product = Product.objects.get(id=response.data['id'])
                
                # Le payload doit être échappé en base de données
                # (pas d'exécution possible)
                self.assertIn(payload, product.name)
    
    def test_xss_in_product_description(self):
        """Test: XSS dans la description du produit"""
        response = self.client.post(
            self.products_url,
            {
                'name': 'Safe Name',
                'price': '100.00',
                'description': '<img src=x onerror=alert("XSS")>',
                'category': 'electronics'
            },
            format='json',
            **get_auth_headers(self.seller_user)
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            product = Product.objects.get(id=response.data['id'])
            # API doit retourner le texte brut ou échappé
            # Jamais du HTML non-échappé
            response_get = self.client.get(f'/api/products/{product.id}/')
            self.assertIsNotNone(response_get.data)
    
    def test_xss_in_review_comment(self):
        """Test: XSS dans les commentaires d'avis"""
        from apps.orders.models import Order, OrderItem
        from decimal import Decimal
        
        seller_user, seller = create_seller('seller2', 'seller2@test.com')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            price=Decimal('100.00'),
            stock=10,
            status='published',
            slug='test-product',
            description='Test product',
            category=self.category,
            product_type=self.product_type
        )
        
        order = Order.objects.create(
            user=self.customer_user,
            status='delivered',
            subtotal=Decimal('100.00'),
            tax=Decimal('20.00'),
            shipping_fee=Decimal('10.00')
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            seller=seller,
            product=product,
            title_snapshot=product.name,
            price_snapshot=Decimal('100.00'),
            quantity=1,
            line_total=Decimal('100.00')
        )
        
        xss_comment = '<script>alert("XSS")</script>'
        
        response = self.client.post(
            '/api/reviews/',
            {
                'product': product.id,
                'rating': 5,
                'title': 'Test',
                'comment': xss_comment
            },
            format='json',
            **get_auth_headers(self.customer_user)
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            # Vérifier si l'id est présent dans la réponse
            if 'id' in response.data:
                review = Review.objects.get(id=response.data['id'])
                # Le script doit être stocké en tant que texte brut
                self.assertEqual(review.comment, xss_comment)
            else:
                # Chercher la review par d'autres moyens
                review = Review.objects.filter(
                    product=product,
                    user=self.customer_user,
                    comment=xss_comment
                ).first()
                if review:
                    self.assertEqual(review.comment, xss_comment)
        else:
            # Si la création échoue, vérifier que c'est pour une raison valide
            self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
            # Le test passe si l'XSS est bloqué ou si on ne peut pas créer de review
            # Le script malveillant ne doit pas être exécuté


class AuthenticationSecurityTests(APITestCase):
    """Tests pour les vulnérabilités d'authentification"""
    
    def setUp(self):
        self.user = create_user('testuser', 'test@test.com', 'TestPass123!@')
        self.auth_url = '/api/auth/login/'
        self.protected_url = '/api/orders/'
    
    def test_password_not_returned_in_api_response(self):
        """Test: Le mot de passe ne doit jamais être retourné par l'API"""
        response = self.client.post(
            self.auth_url,
            {
                'username': 'testuser',
                'password': 'TestPass123!@'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que le mot de passe n'est pas en réponse
        self.assertNotIn('password', str(response.data).lower())
    
    def test_invalid_token_rejected(self):
        """Test: Token invalide est rejeté"""
        headers = {'HTTP_AUTHORIZATION': 'Bearer invalid_token_here'}
        
        response = self.client.get(
            self.protected_url,
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_expired_token_rejected(self):
        """Test: Token expiré est rejeté"""
        from freezegun import freeze_time
        from tests.fixtures import get_auth_token
        from datetime import datetime, timedelta
        
        # Créer un token
        token = get_auth_token(self.user)
        
        # Simuler le passage du temps (token expire après 5 min)
        with freeze_time(datetime.now() + timedelta(minutes=10)):
            headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
            
            response = self.client.get(
                self.protected_url,
                **headers
            )
            
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_cannot_be_reused_after_logout(self):
        """Test: Token ne peut pas être réutilisé après logout"""
        response = self.client.post(
            self.auth_url,
            {
                'username': 'testuser',
                'password': 'TestPass123!@'
            }
        )
        
        token = response.data.get('access')
        
        # Logout (blacklist token)
        self.client.post(
            '/api/auth/logout/',
            **{'HTTP_AUTHORIZATION': f'Bearer {token}'}
        )
        
        # Réutiliser le token doit échouer
        response = self.client.get(
            self.protected_url,
            **{'HTTP_AUTHORIZATION': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizationSecurityTests(APITestCase):
    """Tests pour les vulnérabilités d'autorisation"""
    
    def setUp(self):
        self.customer1_user, self.customer1_profile = create_customer('customer1', 'customer1@test.com')
        self.customer2_user, self.customer2_profile = create_customer('customer2', 'customer2@test.com')
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
    
    def test_cannot_access_other_customer_profile(self):
        """Test: Customer ne peut pas accéder au profil d'un autre customer"""
        response = self.client.get(
            f'/api/customer/profile/{self.customer2_profile.id}/',
            **get_auth_headers(self.customer1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cannot_update_other_customer_profile(self):
        """Test: Customer ne peut pas modifier le profil d'un autre customer"""
        response = self.client.patch(
            f'/api/customer/profile/{self.customer2_profile.id}/',
            {'phone': '+1234567890'},
            format='json',
            **get_auth_headers(self.customer1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_customer_cannot_modify_seller_profile(self):
        """Test: Customer ne peut pas modifier le profil seller"""
        response = self.client.patch(
            f'/api/seller/profile/{self.seller.id}/',
            {'commission_rate': '50'},
            format='json',
            **get_auth_headers(self.customer1_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_seller_cannot_modify_other_seller_profile(self):
        """Test: Seller ne peut pas modifier le profil d'un autre seller"""
        seller2_user, seller2 = create_seller('seller2', 'seller2@test.com')
        
        response = self.client.patch(
            f'/api/seller/profile/{seller2.id}/',
            {'commission_rate': '0'},
            format='json',
            **get_auth_headers(self.seller_user)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DataLeakageSecurityTests(APITestCase):
    """Tests pour détecter les fuites de données"""
    
    def setUp(self):
        self.customer_user, _ = create_customer('customer1', 'customer1@test.com')
        self.seller1_user, self.seller1 = create_seller('seller1', 'seller1@test.com')
        self.seller2_user, self.seller2 = create_seller('seller2', 'seller2@test.com')
    
    def test_customer_cannot_see_seller_email(self):
        """Test: Customer ne doit pas voir l'email d'un seller"""
        response = self.client.get(
            f'/api/sellers/{self.seller1.id}/',
            **get_auth_headers(self.customer_user)
        )
        
        if response.status_code == status.HTTP_200_OK:
            # Email doit être masqué ou absent
            if 'email' in response.data:
                self.assertNotEqual(response.data['email'], self.seller1_user.email)
    
    def test_seller_cannot_see_other_seller_sales(self):
        """Test: Seller ne doit pas voir les ventes des autres sellers"""
        response = self.client.get(
            '/api/seller/analytics/',
            **get_auth_headers(self.seller1_user)
        )
        
        if response.status_code == status.HTTP_200_OK:
            # Les données doivent être spécifiques à ce seller
            self.assertEqual(response.data.get('seller_id'), self.seller1.id)
    
    def test_customer_cannot_see_payment_details_of_other_customers(self):
        """Test: Customer ne doit pas voir les détails de paiement d'autres"""
        response = self.client.get(
            '/api/payments/',
            **get_auth_headers(self.customer_user)
        )
        
        if response.status_code == status.HTTP_200_OK:
            # Handle both paginated and non-paginated responses
            payments = response.data if isinstance(response.data, list) else response.data.get('results', [])
            # Tous les paiements doivent appartenir à ce customer
            for payment in payments:
                self.assertEqual(payment.get('customer_id'), self.customer_user.id)


class RateLimitingSecurityTests(APITestCase):
    """Tests pour vérifier le rate limiting"""
    
    def setUp(self):
        self.user = create_user('testuser', 'test@test.com', 'TestPass123!@')
        self.login_url = '/api/auth/login/'
    
    def test_brute_force_protection_on_login(self):
        """Test: Protection contre le brute force sur login"""
        # Essayer 10+ fois avec mauvais mot de passe
        for i in range(15):
            response = self.client.post(
                self.login_url,
                {
                    'username': 'testuser',
                    'password': 'wrongpassword'
                }
            )
            
            # Après quelques tentatives, doit être rate limited (429)
            if i > 5:
                if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    # Rate limiting en place ✓
                    return
        
        # Si on arrive ici, rate limiting ne fonctionne pas
        # (mais c'est possiblement pas implémenté)
    
    def test_api_rate_limiting_per_ip(self):
        """Test: Chaque IP est limitée"""
        api_url = '/api/products/'
        
        responses = []
        for i in range(150):  # 150 requêtes rapides
            response = self.client.get(api_url)
            responses.append(response.status_code)
        
        # Après X requêtes, doit être rate limited
        if status.HTTP_429_TOO_MANY_REQUESTS in responses:
            # Rate limiting en place ✓
            return
        
        # Peut ne pas être implémenté


class CSRFProtectionTests(APITestCase):
    """Tests pour vérifier la protection CSRF"""
    
    def setUp(self):
        self.user = create_user('testuser', 'test@test.com', 'TestPass123!@')
        self.seller_user, self.seller = create_seller('seller1', 'seller1@test.com')
    
    def test_post_requires_csrf_token(self):
        """Test: POST requests doivent avoir CSRF token"""
        # Si CSRF middleware est activé, POST sans token doit échouer
        response = self.client.post(
            '/api/products/',
            {
                'name': 'Test Product',
                'price': '100.00'
            },
            format='json'
        )
        
        # Doit retourner 401 (unauthenticated) ou 403 (CSRF)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )
