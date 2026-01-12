"""
Serializers for returns app.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import ReturnRequest


class ReturnRequestSerializer(serializers.ModelSerializer):
    """Serializer for return requests with refund tracking"""
    
    order_item_id = serializers.IntegerField(source='order_item.id', read_only=True)
    product_name = serializers.CharField(source='order_item.product.name', read_only=True)
    customer_name = serializers.CharField(source='user.get_full_name', read_only=True)
    seller_name = serializers.CharField(source='seller.shop_name', read_only=True, allow_null=True)
    
    class Meta:
        model = ReturnRequest
        fields = [
            'id', 'order_item', 'order_item_id', 'product_name', 'user',
            'customer_name', 'seller', 'seller_name', 'reason', 'description',
            'status', 'refund_status', 'refund_amount', 'deduction_amount',
            'deduction_reason', 'inspected_by', 'inspected_at', 'inspection_notes',
            'tracking_number', 'carrier', 'shipping_label', 'responded_by',
            'response_note', 'refund_initiated_by', 'refund_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'refund_status', 'inspected_at',
            'created_at', 'updated_at'
        ]

from apps.returns.models import ReturnRequest
from apps.orders.models import OrderItem


class ReturnRequestSerializer(serializers.ModelSerializer):
    """Return request serializer."""
    
    order_reference = serializers.CharField(
        source='order_item.order.reference', 
        read_only=True
    )
    product_title = serializers.CharField(
        source='order_item.title_snapshot',
        read_only=True
    )
    seller_name = serializers.CharField(
        source='order_item.seller.shop_name',
        read_only=True
    )
    
    class Meta:
        model = ReturnRequest
        fields = [
            'id',
            'order_item',
            'order_reference',
            'product_title',
            'seller_name',
            'reason',
            'description',
            'status',
            'response_note',
            'created_at',
            'responded_at',
        ]
        read_only_fields = [
            'id', 'status', 'response_note', 
            'created_at', 'responded_at'
        ]


class CreateReturnRequestSerializer(serializers.ModelSerializer):
    """Create return request serializer."""
    
    class Meta:
        model = ReturnRequest
        fields = ['order_item', 'reason', 'description', 'status']
        read_only_fields = ['status']
    
    def validate_order_item(self, value):
        user = self.context['request'].user
        
        # Check ownership
        if value.order.user != user:
            raise serializers.ValidationError("This order item does not belong to you.")
        
        # Check order status (must be delivered)
        if value.order.status != 'delivered':
            raise serializers.ValidationError(
                "Return requests can only be made for delivered orders."
            )
        
        # Check for existing return request
        if value.return_requests.exclude(status='rejected').exists():
            raise serializers.ValidationError(
                "A return request already exists for this item."
            )
        
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UpdateReturnRequestSerializer(serializers.ModelSerializer):
    """Update return request for seller/admin."""
    
    class Meta:
        model = ReturnRequest
        fields = ['status', 'response_note']
    
    def validate_status(self, value):
        instance = self.instance
        if not instance:
            return value
        
        valid_transitions = {
            'initiated': ['approved', 'rejected'],
            'requested': ['approved', 'rejected'],
            'approved': ['received'],
            'received': ['refunded'],
            'rejected': [],
            'refunded': [],
        }
        
        allowed = valid_transitions.get(instance.status, [])
        if value != instance.status and value not in allowed:
            raise serializers.ValidationError(
                f"Cannot transition from '{instance.status}' to '{value}'."
            )
        
        return value
    
    def update(self, instance, validated_data):
        if 'status' in validated_data and validated_data['status'] != instance.status:
            instance.responded_at = timezone.now()
            instance.responded_by = self.context['request'].user
        return super().update(instance, validated_data)
