"""
Serializers for payments app.
"""
from rest_framework import serializers
from .models import Payment, Refund


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for payment refunds"""
    
    initiated_by_name = serializers.CharField(source='initiated_by.get_full_name', read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'reason', 'provider_refund_id',
            'status', 'initiated_by', 'initiated_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'provider_refund_id', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Stripe payments with refund tracking"""
    
    order_ref = serializers.CharField(source='order.reference', read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)
    total_refunded = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_ref', 'provider', 'provider_intent_id',
            'provider_charge_id', 'amount', 'currency', 'status',
            'client_secret', 'metadata', 'error_message', 'paid_at',
            'created_at', 'updated_at', 'refunds', 'total_refunded',
            'remaining_amount'
        ]
        read_only_fields = [
            'id', 'provider_intent_id', 'provider_charge_id',
            'client_secret', 'error_message', 'paid_at',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'provider_charge_id': {'write_only': True},
            'metadata': {'required': False}
        }
    
    def get_total_refunded(self, obj):
        from decimal import Decimal
        refunds = Refund.objects.filter(payment=obj, status='succeeded')
        return sum(r.amount for r in refunds) or Decimal('0.00')
    
    def get_remaining_amount(self, obj):
        from decimal import Decimal
        refunds = Refund.objects.filter(payment=obj, status='succeeded')
        total_refunded = sum(r.amount for r in refunds) or Decimal('0.00')
        return obj.amount - total_refunded


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer for customer view."""
    
    order_reference = serializers.CharField(source='order.reference', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'order_reference',
            'provider',
            'amount',
            'currency',
            'status',
            'created_at',
            'paid_at',
        ]
        read_only_fields = fields


class CreatePaymentIntentSerializer(serializers.Serializer):
    """Serializer for creating a payment intent."""
    
    order_id = serializers.IntegerField()
    
    def validate_order_id(self, value):
        from apps.orders.models import Order
        
        user = self.context.get('request').user
        try:
            order = Order.objects.get(pk=value, user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
        
        if order.payment_status == 'paid':
            raise serializers.ValidationError("Order is already paid.")
        
        if order.status == 'cancelled':
            raise serializers.ValidationError("Cannot pay for cancelled order.")
        
        return value


class PaymentIntentResponseSerializer(serializers.Serializer):
    """Response serializer for payment intent creation."""
    
    payment_id = serializers.IntegerField()
    client_secret = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()


class RefundSerializer(serializers.ModelSerializer):
    """Refund serializer for admin view."""
    
    class Meta:
        model = Refund
        fields = [
            'id',
            'payment',
            'amount',
            'reason',
            'status',
            'initiated_by',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'initiated_by', 'created_at']


class CreateRefundSerializer(serializers.Serializer):
    """Serializer for creating a refund."""
    
    payment_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(pk=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")
        
        if payment.status != 'succeeded':
            raise serializers.ValidationError("Can only refund succeeded payments.")
        
        return value
