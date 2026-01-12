"""
Tests API pour l'authentification et JWT
Couvre: login, logout, token refresh, /api/auth/me/
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.customers.models import CustomerProfile
from tests.fixtures import (
    create_user, get_auth_headers, create_customer, create_seller
)

User = get_user_model()


class JWTAuthenticationTests(APITestCase):
    """Tests pour l'authentification JWT"""
    
    def setUp(self):
        self.user = create_user(
            username='testuser',
            email='testuser@test.com',
            password='TestPass123!@'
        )
        self.login_url = '/api/auth/login/'
        self.refresh_url = '/api/auth/token/refresh/'
        self.me_url = '/api/auth/me/'
    
    def test_jwt_login_success(self):
        """Test login avec credentials corrects"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!@'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_jwt_login_invalid_credentials(self):
        """Test login avec mauvais password"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword123!@'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_jwt_login_nonexistent_user(self):
        """Test login avec user inexistant"""
        response = self.client.post(self.login_url, {
            'username': 'nonexistent',
            'password': 'SomePass123!@'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_jwt_refresh_token(self):
        """Test refresh du token"""
        # Obtenir le refresh token
        login_response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!@'
        })
        refresh_token = login_response.data['refresh']
        
        # Refresh le token
        response = self.client.post(self.refresh_url, {
            'refresh': refresh_token
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_jwt_refresh_invalid_token(self):
        """Test refresh avec token invalide"""
        response = self.client.post(self.refresh_url, {
            'refresh': 'invalid_token_here'
        })
        
        # 400 Bad Request or 401 Unauthorized are both acceptable
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])
    
    def test_api_auth_me_authenticated(self):
        """Test /api/auth/me/ avec user authentifié"""
        response = self.client.get(self.me_url, **get_auth_headers(self.user))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'testuser@test.com')
    
    def test_api_auth_me_unauthenticated(self):
        """Test /api/auth/me/ sans authentification"""
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_api_auth_me_returns_user_role(self):
        """Test que /api/auth/me/ retourne le rôle"""
        response = self.client.get(self.me_url, **get_auth_headers(self.user))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'customer')
    
    def test_api_auth_me_seller_role(self):
        """Test /api/auth/me/ pour un vendeur"""
        seller_user = create_user(
            username='seller',
            email='seller@test.com',
            role='seller'
        )
        
        response = self.client.get(self.me_url, **get_auth_headers(seller_user))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'seller')
    
    def test_expired_token_rejected(self):
        """Test que token expiré est rejeté"""
        from rest_framework_simplejwt.settings import api_settings
        from datetime import timedelta
        from freezegun import freeze_time
        
        # Créer un token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        # Avancer le temps au-delà de l'expiration
        with freeze_time('2099-01-01'):
            response = self.client.get(
                self.me_url,
                HTTP_AUTHORIZATION=f'Bearer {access_token}'
            )
            
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_protected_endpoint_without_token(self):
        """Test qu'on ne peut pas accéder à un endpoint protégé sans token"""
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
    
    def test_access_protected_endpoint_with_invalid_token(self):
        """Test qu'on ne peut pas accéder avec un token invalide"""
        response = self.client.get(
            self.me_url,
            HTTP_AUTHORIZATION='Bearer invalid_token_here'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RegistrationTests(APITestCase):
    """Tests pour l'enregistrement d'utilisateurs"""
    
    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
    
    def test_customer_registration_success(self):
        """Test enregistrement client réussi"""
        response = self.client.post(self.register_url, {
            'username': 'newcustomer',
            'email': 'newcustomer@test.com',
            'password': 'SecurePass123!@',
            'password_confirm': 'SecurePass123!@',
            'first_name': 'John',
            'last_name': 'Doe'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newcustomer').exists())
        
        # Vérifier qu'on peut se connecter
        login_response = self.client.post(self.login_url, {
            'username': 'newcustomer',
            'password': 'SecurePass123!@'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
    
    def test_registration_duplicate_email(self):
        """Test enregistrement avec email déjà existant"""
        create_user(username='existing', email='existing@test.com')
        
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'existing@test.com',
            'password': 'SecurePass123!@',
            'password_confirm': 'SecurePass123!@'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_duplicate_username(self):
        """Test enregistrement avec username déjà existant"""
        create_user(username='existing', email='existing@test.com')
        
        response = self.client.post(self.register_url, {
            'username': 'existing',
            'email': 'different@test.com',
            'password': 'SecurePass123!@',
            'password_confirm': 'SecurePass123!@'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_password_mismatch(self):
        """Test enregistrement avec passwords différents"""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'SecurePass123!@',
            'password_confirm': 'DifferentPass123!@'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_creates_customer_profile(self):
        """Test que l'enregistrement crée aussi CustomerProfile"""
        response = self.client.post(self.register_url, {
            'username': 'newcustomer',
            'email': 'newcustomer@test.com',
            'password': 'SecurePass123!@',
            'password_confirm': 'SecurePass123!@'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='newcustomer')
        self.assertTrue(
            CustomerProfile.objects.filter(user=user).exists()
        )
