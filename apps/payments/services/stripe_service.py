"""
Stripe payment service.
Handles PaymentIntent creation and webhook processing.
"""
import logging
from decimal import Decimal
from typing import Optional, Dict, Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class StripeService:
    """
    Service for Stripe payment operations.
    Uses environment variables for configuration.
    """
    
    def __init__(self):
        self.stripe = None
        self._initialize_stripe()
    
    def _initialize_stripe(self):
        """Initialize Stripe with API key from settings."""
        try:
            import stripe
            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
            if not stripe.api_key:
                logger.warning("STRIPE_SECRET_KEY not configured")
            self.stripe = stripe
        except ImportError:
            logger.error("Stripe library not installed. Run: pip install stripe")
            self.stripe = None
    
    def create_payment_intent(
        self,
        order,
        currency: str = 'eur'
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Stripe PaymentIntent for an order.
        
        Args:
            order: Order model instance
            currency: Currency code (lowercase for Stripe)
        
        Returns:
            Dict with intent_id, client_secret, or None on failure
        """
        if not self.stripe:
            logger.error("Stripe not initialized")
            return None
        
        # Convert amount to cents (Stripe uses smallest currency unit)
        amount_cents = int(order.total_amount * 100)
        
        try:
            intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata={
                    'order_id': order.id,
                    'order_reference': order.reference,
                    'customer_email': order.user.email,
                },
                # Idempotency key to prevent duplicate charges
                idempotency_key=f"order_{order.id}_{order.reference}",
            )
            
            return {
                'intent_id': intent.id,
                'client_secret': intent.client_secret,
                'status': intent.status,
            }
        
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error creating PaymentIntent: {e}")
            return None
    
    def retrieve_payment_intent(self, intent_id: str) -> Optional[Dict]:
        """Retrieve a PaymentIntent by ID."""
        if not self.stripe:
            return None
        
        try:
            intent = self.stripe.PaymentIntent.retrieve(intent_id)
            return {
                'id': intent.id,
                'status': intent.status,
                'amount': intent.amount,
                'currency': intent.currency,
                'metadata': dict(intent.metadata),
            }
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving PaymentIntent: {e}")
            return None
    
    def create_refund(
        self,
        payment_intent_id: str,
        amount_cents: Optional[int] = None,
        reason: str = 'requested_by_customer'
    ) -> Optional[Dict]:
        """
        Create a refund for a PaymentIntent.
        
        Args:
            payment_intent_id: Stripe PaymentIntent ID
            amount_cents: Amount to refund in cents (None = full refund)
            reason: Reason for refund
        
        Returns:
            Dict with refund details or None on failure
        """
        if not self.stripe:
            return None
        
        try:
            refund_params = {
                'payment_intent': payment_intent_id,
                'reason': reason,
            }
            if amount_cents:
                refund_params['amount'] = amount_cents
            
            refund = self.stripe.Refund.create(**refund_params)
            
            return {
                'refund_id': refund.id,
                'status': refund.status,
                'amount': refund.amount,
            }
        
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {e}")
            return None
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        sig_header: str
    ) -> Optional[Dict]:
        """
        Verify and parse Stripe webhook signature.
        
        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value
        
        Returns:
            Parsed event dict or None if invalid
        """
        if not self.stripe:
            return None
        
        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        if not webhook_secret:
            logger.error("STRIPE_WEBHOOK_SECRET not configured")
            return None
        
        try:
            event = self.stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return {
                'type': event.type,
                'data': event.data.object,
            }
        
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return None
        except self.stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return None


def process_payment_succeeded(payment_intent_data: Dict) -> bool:
    """
    Process a successful payment webhook.
    Updates Order and Payment status.
    
    Args:
        payment_intent_data: PaymentIntent object from webhook
    
    Returns:
        True if processed successfully
    """
    from apps.payments.models import Payment
    from apps.orders.models import Order
    
    # Support both test format and real Stripe format
    intent_id = payment_intent_data.get('id') or payment_intent_data.get('stripe_payment_intent_id')
    metadata = payment_intent_data.get('metadata', {})
    order_id = metadata.get('order_id') or payment_intent_data.get('order_id')
    
    if not order_id and not intent_id:
        logger.error(f"No order_id or intent_id in payment data")
        return False
    
    # If we have intent_id but no order_id, try to find order from existing payment
    if intent_id and not order_id:
        try:
            existing_payment = Payment.objects.filter(provider_intent_id=intent_id).first()
            if existing_payment:
                order_id = existing_payment.order_id
        except Exception:
            pass
    
    if not order_id:
        logger.error(f"No order_id found for intent: {intent_id}")
        return False
    
    try:
        with transaction.atomic():
            # Get order first
            order = Order.objects.select_for_update().get(pk=order_id)
            
            # Calculate amount (handle both cents and decimal)
            amount_raw = payment_intent_data.get('amount', 0)
            if isinstance(amount_raw, int) and amount_raw > 1000:
                # Assume cents if integer > 1000
                amount = Decimal(amount_raw) / 100
            else:
                amount = Decimal(str(amount_raw))
            
            # Get or create payment with idempotency
            payment, created = Payment.objects.select_for_update().get_or_create(
                provider_intent_id=intent_id,
                defaults={
                    'order': order,
                    'amount': amount,
                    'currency': payment_intent_data.get('currency', 'usd'),
                    'provider': 'stripe',
                    'status': 'succeeded',
                    'paid_at': timezone.now(),
                }
            )
            
            # Update payment if it already existed but wasn't completed
            if not created and payment.status != 'succeeded':
                payment.status = 'succeeded'
                payment.paid_at = timezone.now()
                payment.save()
            
            # Update order only if not already paid
            if order.payment_status != 'paid':
                order.payment_status = 'paid'
                order.paid_at = timezone.now()
                if order.status == 'pending':
                    order.status = 'paid'
                order.save()
                
                # Update seller orders to processing
                order.seller_orders.filter(status='pending').update(status='processing')
            
            logger.info(f"Payment succeeded for order {order.reference}")
            return True
    
    except Order.DoesNotExist:
        logger.error(f"Order not found: {order_id}")
        return False
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        return False


def process_payment_failed(payment_intent_data: Dict) -> bool:
    """
    Process a failed payment webhook.
    
    Args:
        payment_intent_data: PaymentIntent object from webhook
    
    Returns:
        True if processed successfully
    """
    from apps.payments.models import Payment
    from apps.orders.models import Order
    
    intent_id = payment_intent_data.get('id')
    error = payment_intent_data.get('last_payment_error', {})
    
    try:
        payment = Payment.objects.get(provider_intent_id=intent_id)
        payment.status = 'failed'
        payment.error_message = error.get('message', 'Payment failed')
        payment.save()
        
        logger.info(f"Payment failed for order {payment.order.reference}")
        return True
    
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for intent: {intent_id}")
        return False


# Singleton instance
stripe_service = StripeService()
