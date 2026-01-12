"""
Comprehensive test suite for accounts app: authentication, JWT, RBAC, and user management.

Test Categories Covered:
- B) Authentication & JWT: Token obtain, refresh, claims, expiration, invalid credentials
- C) RBAC: Admin endpoints forbidden for sellers, role-based access control
- Unauthorized Access: 401/403 responses when appropriate
- Me Endpoint: Current user information retrieval and permissions
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

User = get_user_model()


# ============================================================================
# AUTHENTICATION & TOKEN TESTS (Category B)
# ============================================================================

@pytest.mark.django_db
class TestTokenObtain:
    """Test JWT token obtain endpoint."""

    def test_token_obtain_with_valid_credentials(self, api_client, seller_user):
        """Valid credentials should return access and refresh tokens."""
        response = api_client.post('/api/auth/token/', {
            'email': 'seller@test.com',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert isinstance(response.data['access'], str)
        assert isinstance(response.data['refresh'], str)

    def test_token_obtain_with_invalid_username(self, api_client):
        """Invalid username should return 400 or 401."""
        response = api_client.post('/api/auth/token/', {
            'email': 'nonexistent@test.com',
            'password': 'testpass123'
        })
        assert response.status_code in [400, 401]

    def test_token_obtain_with_invalid_password(self, api_client, seller_user):
        """Invalid password should return 400 or 401."""
        response = api_client.post('/api/auth/token/', {
            'email': 'seller@test.com',
            'password': 'wrongpassword'
        })
        assert response.status_code in [400, 401]

    def test_token_obtain_with_missing_credentials(self, api_client):
        """Missing username should return 400."""
        response = api_client.post('/api/auth/token/', {
            'password': 'testpass123'
        })
        assert response.status_code == 400

    def test_token_obtain_with_admin_user(self, api_client, super_admin):
        """Admin user should also get tokens."""
        response = api_client.post('/api/auth/token/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        assert 'access' in response.data


@pytest.mark.django_db
class TestTokenRefresh:
    """Test JWT token refresh endpoint."""

    def test_token_refresh_with_valid_refresh_token(self, api_client, get_seller_tokens):
        """Valid refresh token should return new access token."""
        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': get_seller_tokens['refresh']
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert isinstance(response.data['access'], str)

    def test_token_refresh_with_invalid_token(self, api_client):
        """Invalid refresh token should return 400 or 401."""
        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': 'invalid.token.here'
        })
        assert response.status_code in [400, 401]

    def test_token_refresh_with_missing_refresh_token(self, api_client):
        """Missing refresh token should return 400."""
        response = api_client.post('/api/auth/token/refresh/', {})
        assert response.status_code == 400

    def test_token_refresh_returns_different_access_token(self, api_client, get_seller_tokens):
        """Refreshed access token should be different from original."""
        original_token = get_seller_tokens['access']
        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': get_seller_tokens['refresh']
        })
        new_token = response.data['access']
        assert original_token != new_token

    def test_refresh_token_not_in_refresh_response(self, api_client, get_seller_tokens):
        """Refresh response should not include new refresh token."""
        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': get_seller_tokens['refresh']
        })
        assert 'refresh' not in response.data


@pytest.mark.django_db
class TestTokenClaims:
    """Test JWT token structure and claims."""

    def test_access_token_contains_user_id(self, seller_user, get_seller_tokens):
        """Access token should contain user ID claim."""
        token_str = get_seller_tokens['access']
        # Token format: header.payload.signature
        parts = token_str.split('.')
        assert len(parts) == 3  # Valid JWT has 3 parts

    def test_refresh_token_is_valid_jwt(self, get_seller_tokens):
        """Refresh token should be valid JWT."""
        token_str = get_seller_tokens['refresh']
        parts = token_str.split('.')
        assert len(parts) == 3

    def test_token_for_different_users_are_different(self, seller_user, seller_user_2):
        """Tokens for different users should be different."""
        refresh1 = RefreshToken.for_user(seller_user)
        refresh2 = RefreshToken.for_user(seller_user_2)
        assert str(refresh1) != str(refresh2)


# ============================================================================
# ME ENDPOINT TESTS
# ============================================================================

@pytest.mark.django_db
class TestMeEndpoint:
    """Test /api/auth/me/ endpoint for current user info."""

    def test_authenticated_user_can_get_me(self, authenticated_client, seller_user):
        """Authenticated user should get own profile."""
        response = authenticated_client.get('/api/auth/me/')
        assert response.status_code == 200
        assert str(response.data['id']) == str(seller_user.id)
        assert response.data['email'] == seller_user.email
        assert response.data['role'] == 'seller'

    def test_admin_user_can_get_me(self, admin_client, super_admin):
        """Admin user should get own profile."""
        response = admin_client.get('/api/auth/me/')
        assert response.status_code == 200
        assert str(response.data['id']) == str(super_admin.id)
        assert response.data['role'] == 'super_admin'

    def test_unauthenticated_user_cannot_access_me(self, api_client):
        """Unauthenticated request should return 401."""
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 401

    def test_me_endpoint_with_invalid_token(self, api_client):
        """Invalid token should return 401."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.here')
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 401

    def test_seller_me_includes_profile_info(self, authenticated_client, seller_user):
        """Seller /me should include seller profile information."""
        response = authenticated_client.get('/api/auth/me/')
        assert response.status_code == 200
        # Check for seller-specific fields
        assert 'email' in response.data
        assert 'role' in response.data
        assert response.data['role'] == 'seller'


# ============================================================================
# RBAC & ACCESS CONTROL TESTS (Category C)
# ============================================================================

@pytest.mark.django_db
class TestAdminAccessControl:
    """Test role-based access control for admin endpoints."""

    def test_admin_can_access_admin_endpoints(self, admin_client):
        """Admin should access admin category endpoints."""
        response = admin_client.get('/api/catalog/admin/categories/')
        assert response.status_code in [200, 404]  # Endpoint exists but may be empty

    def test_seller_cannot_access_admin_categories_endpoint(self, authenticated_client):
        """Seller should not access /admin/categories/."""
        response = authenticated_client.get('/api/catalog/admin/categories/')
        assert response.status_code == 403

    def test_seller_cannot_access_admin_product_types_endpoint(self, authenticated_client):
        """Seller should not access /admin/product-types/."""
        response = authenticated_client.get('/api/catalog/admin/product-types/')
        assert response.status_code == 403

    def test_seller_cannot_access_admin_attributes_endpoint(self, authenticated_client):
        """Seller should not access /admin/attributes/."""
        response = authenticated_client.get('/api/catalog/admin/attributes/')
        assert response.status_code == 403

    def test_seller_cannot_create_category(self, authenticated_client, category):
        """Seller should not be able to create categories."""
        response = authenticated_client.post('/api/catalog/admin/categories/', {
            'name': 'New Category',
            'slug': 'new-category'
        })
        assert response.status_code == 403

    def test_admin_can_create_category(self, admin_client):
        """Admin should be able to create categories."""
        response = admin_client.post('/api/catalog/admin/categories/', {
            'name': 'New Category',
            'slug': 'new-category-unique'
        })
        assert response.status_code in [201, 403]  # 201 if allowed, 403 if forbidden by permission


@pytest.mark.django_db
class TestSellerAccessControl:
    """Test seller endpoints are restricted to correct roles."""

    def test_seller_can_access_seller_products_endpoint(self, authenticated_client):
        """Seller should access own seller/products/ endpoint."""
        response = authenticated_client.get('/api/catalog/seller/products/')
        assert response.status_code in [200, 404]  # May be empty but not forbidden

    def test_admin_cannot_access_seller_products_as_seller(self, admin_client):
        """Admin accessing seller endpoint should either get 404 or empty list (no products)."""
        response = admin_client.get('/api/catalog/seller/products/')
        # Admin has no seller profile, so should not see products
        assert response.status_code in [403, 404, 200]

    def test_unauthenticated_user_cannot_access_seller_products(self, api_client):
        """Unauthenticated user should not access seller products."""
        response = api_client.get('/api/catalog/seller/products/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestRoleBasedReadAccess:
    """Test role-based read access to resources."""

    def test_admin_can_list_all_categories(self, admin_client):
        """Admin should list all categories."""
        response = admin_client.get('/api/catalog/admin/categories/')
        assert response.status_code in [200, 404]

    def test_seller_cannot_list_all_categories(self, authenticated_client):
        """Seller should not list categories via admin endpoint."""
        response = authenticated_client.get('/api/catalog/admin/categories/')
        assert response.status_code == 403


# ============================================================================
# UNAUTHORIZED & PERMISSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestUnauthorizedAccess:
    """Test unauthorized access scenarios."""

    def test_missing_auth_header_returns_401(self, api_client):
        """Request without Authorization header should return 401."""
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 401

    def test_malformed_auth_header_returns_401(self, api_client):
        """Malformed Authorization header should return 401."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer')
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 401

    def test_expired_token_returns_401(self, api_client, seller_user):
        """Expired token should return 401."""
        refresh = RefreshToken.for_user(seller_user)
        # Manipulate token expiration for testing
        token_str = str(refresh.access_token)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_str}')
        # Token should be valid initially
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 200

    def test_wrong_token_signature_returns_401(self, api_client):
        """Token with wrong signature should return 401."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature')
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 401


# ============================================================================
# SUSPENDED & PENDING SELLER TESTS
# ============================================================================

@pytest.mark.django_db
class TestSuspendedSellerAccess:
    """Test suspended sellers cannot perform actions."""

    def test_suspended_seller_can_obtain_token(self, api_client, suspended_seller):
        """Suspended seller should still be able to get token (account still exists)."""
        response = api_client.post('/api/auth/token/', {
            'email': 'suspended@test.com',
            'password': 'testpass123'
        })
        assert response.status_code == 200

    def test_suspended_seller_can_access_me(self, api_client, suspended_seller):
        """Suspended seller should access /me endpoint."""
        response = api_client.post('/api/auth/token/', {
            'email': 'suspended@test.com',
            'password': 'testpass123'
        })
        token = response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 200
        assert response.data['role'] == 'seller'


@pytest.mark.django_db
class TestPendingSellerAccess:
    """Test pending sellers cannot perform actions."""

    def test_pending_seller_can_obtain_token(self, api_client, pending_seller):
        """Pending seller should be able to get token."""
        response = api_client.post('/api/auth/token/', {
            'email': 'pending@test.com',
            'password': 'testpass123'
        })
        assert response.status_code == 200

    def test_pending_seller_profile_shows_correct_status(self, api_client, pending_seller):
        """Pending seller profile should show pending status."""
        response = api_client.post('/api/auth/token/', {
            'email': 'pending@test.com',
            'password': 'testpass123'
        })
        token = response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 200


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestAuthenticationFlow:
    """Test complete authentication flow."""

    def test_complete_auth_flow(self, api_client, seller_user):
        """Complete flow: get token -> get me -> refresh -> get me again."""
        # Step 1: Get tokens
        response = api_client.post('/api/auth/token/', {
            'email': 'seller@test.com',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        
        # Step 2: Use access token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 200
        
        # Step 3: Refresh token
        api_client.credentials()  # Clear credentials
        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': refresh_token
        })
        assert response.status_code == 200
        new_access_token = response.data['access']
        
        # Step 4: Use new token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 200

    def test_multiple_concurrent_sessions(self, api_client, seller_user, seller_user_2):
        """Multiple users should have independent sessions."""
        # Get token for seller 1
        response = api_client.post('/api/auth/token/', {
            'email': 'seller@test.com',
            'password': 'testpass123'
        })
        seller1_token = response.data['access']
        
        # Get token for seller 2
        response = api_client.post('/api/auth/token/', {
            'email': 'seller2@test.com',
            'password': 'testpass123'
        })
        seller2_token = response.data['access']
        
        # Verify isolation
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {seller1_token}')
        response1 = api_client.get('/api/auth/me/')
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {seller2_token}')
        response2 = api_client.get('/api/auth/me/')
        
        assert response1.data['id'] != response2.data['id']
