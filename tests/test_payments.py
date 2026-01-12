"""
Tests for the payments app.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.orders.models import Order
from apps.payments.models import Payment, Refund


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
def order_with_payment(db, customer_user):
    """Create an order for payment tests."""
    order = Order.objects.create(
        user=customer_user,
        reference='TEST-0001',
        status='pending',
        payment_status='unpaid',
        subtotal=Decimal('100.00'),
        total_amount=Decimal('100.00'),
        currency='EUR',
        shipping_address={
            'name': 'Test User',
            'address': '123 Test St',
            'city': 'Paris',
            'country': 'FR',
            'postal_code': '75001',
        },
    )
    return order


@pytest.mark.django_db
class TestPaymentModel:
    """Tests for Payment model."""
    
    def test_create_payment(self, order_with_payment):
        """Test creating a payment."""
        payment = Payment.objects.create(
            order=order_with_payment,
            provider='stripe',
            provider_intent_id='pi_test_123',
            amount=order_with_payment.total_amount,
            currency='EUR',
            status='pending',
        )
        
        assert payment.pk is not None
        assert payment.order == order_with_payment
        assert payment.amount == Decimal('100.00')
        assert f"Payment {payment.pk}" in str(payment)


@pytest.mark.django_db
class TestRefundModel:
    """Tests for Refund model."""
    
    def test_create_refund(self, order_with_payment):
        """Test creating a refund."""
        payment = Payment.objects.create(
            order=order_with_payment,
            provider='stripe',
            provider_intent_id='pi_test_123',
            amount=Decimal('100.00'),
            currency='EUR',
            status='succeeded',
        )
        
        refund = Refund.objects.create(
            payment=payment,
            amount=Decimal('50.00'),
            reason='Customer request',
            status='pending',
        )
        
        assert refund.pk is not None
        assert refund.payment == payment
        assert refund.amount == Decimal('50.00')


@pytest.mark.django_db
class TestPaymentListView:
    """Tests for payment list endpoint."""
    
    def test_list_own_payments(self, api_client, customer_user, order_with_payment):
        """Test customer can list their own payments."""
        Payment.objects.create(
            order=order_with_payment,
            provider='stripe',
            provider_intent_id='pi_test_123',
            amount=Decimal('100.00'),
            currency='EUR',
            status='succeeded',
        )
        
        api_client.force_authenticate(user=customer_user)
        response = api_client.get('/api/payments/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_unauthenticated_access_denied(self, api_client):
        """Test unauthenticated user cannot access payments."""
        response = api_client.get('/api/payments/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
