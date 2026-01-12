"""
Views for payments app.
"""
import logging
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from apps.payments.models import Payment
from apps.payments.serializers import (
    PaymentSerializer,
    CreatePaymentIntentSerializer,
    PaymentIntentResponseSerializer,
)
from apps.payments.services.stripe_service import (
    stripe_service,
    process_payment_succeeded,
    process_payment_failed,
)
from apps.orders.models import Order

logger = logging.getLogger(__name__)


class CreatePaymentIntentView(views.APIView):
    """
    Create a Stripe PaymentIntent for an order.
    
    POST /api/payments/create-intent/
    
    Payload:
    {
        "order_id": 1
    }
    
    Response:
    {
        "payment_id": 1,
        "client_secret": "pi_xxx_secret_xxx",
        "amount": "99.99",
        "currency": "EUR"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreatePaymentIntentSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        order = Order.objects.get(pk=order_id, user=request.user)
        
        # Check for existing pending payment
        existing_payment = Payment.objects.filter(
            order=order,
            status__in=['created', 'pending']
        ).first()
        
        if existing_payment and existing_payment.client_secret:
            return Response({
                'payment_id': existing_payment.id,
                'client_secret': existing_payment.client_secret,
                'amount': str(existing_payment.amount),
                'currency': existing_payment.currency,
            })
        
        # Create Stripe PaymentIntent
        result = stripe_service.create_payment_intent(
            order=order,
            currency=order.currency.lower()
        )
        
        if not result:
            return Response(
                {'error': 'Failed to create payment intent'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create Payment record
        payment = Payment.objects.create(
            order=order,
            provider='stripe',
            provider_intent_id=result['intent_id'],
            client_secret=result['client_secret'],
            amount=order.total_amount,
            currency=order.currency,
            status='created'
        )
        
        return Response({
            'payment_id': payment.id,
            'client_secret': result['client_secret'],
            'amount': str(order.total_amount),
            'currency': order.currency,
        }, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(views.APIView):
    """
    Handle Stripe webhooks.
    
    POST /api/payments/webhook/
    
    Verifies Stripe signature and processes events.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # No auth for webhooks
    
    def post(self, request):
        # In test mode (no STRIPE_SECRET_KEY), accept webhooks without signature
        if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY == 'test_key':
            # Test mode: use request data directly
            event_data = request.data
            success = process_payment_succeeded(event_data)
            if success:
                return Response({'received': True})
            else:
                return Response(
                    {'error': 'Failed to process payment'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Production mode: verify Stripe signature
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        
        if not sig_header:
            logger.warning("Missing Stripe signature header")
            return Response(
                {'error': 'Missing signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify signature
        event = stripe_service.verify_webhook_signature(payload, sig_header)
        
        if not event:
            return Response(
                {'error': 'Invalid signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event_type = event.get('type')
        event_data = event.get('data', {})
        
        logger.info(f"Received Stripe webhook: {event_type}")
        
        # Handle different event types
        if event_type == 'payment_intent.succeeded':
            success = process_payment_succeeded(event_data)
            if not success:
                return Response(
                    {'error': 'Failed to process payment'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        elif event_type == 'payment_intent.payment_failed':
            process_payment_failed(event_data)
        
        # Acknowledge receipt of webhook
        return Response({'received': True})


class PaymentListView(views.APIView):
    """
    List payments for the authenticated user.
    
    GET /api/payments/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        payments = Payment.objects.filter(
            order__user=request.user
        ).select_related('order').order_by('-created_at')
        
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
