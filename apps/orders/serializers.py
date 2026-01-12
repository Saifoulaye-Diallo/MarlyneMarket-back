"""
Serializers for orders app.
"""
from decimal import Decimal
from rest_framework import serializers
from .models import Order, OrderItem, SellerOrder


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    seller_name = serializers.CharField(source='seller.shop_name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_name', 'seller', 'seller_name',
            'title_snapshot', 'price_snapshot', 'quantity', 'line_total',
            'created_at'
        ]
        read_only_fields = ['id', 'line_total', 'created_at']


class SellerOrderSerializer(serializers.ModelSerializer):
    """Serializer for seller-specific order view"""
    
    seller_name = serializers.CharField(source='seller.shop_name', read_only=True)
    order_ref = serializers.CharField(source='order.reference', read_only=True)
    
    class Meta:
        model = SellerOrder
        fields = [
            'id', 'order', 'order_ref', 'seller', 'seller_name', 'seller_status',
            'subtotal', 'tracking_number', 'carrier', 'shipped_at', 'delivered_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'subtotal', 'shipped_at', 'delivered_at',
            'created_at', 'updated_at'
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders with multi-seller support"""
    
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    seller_orders = SellerOrderSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_name', 'reference', 'status',
            'payment_status', 'subtotal', 'tax_amount', 'shipping_fee',
            'discount_amount', 'total_amount', 'shipping_address',
            'billing_address', 'coupon_code', 'customer_note', 'admin_note',
            'created_at', 'updated_at', 'items', 'seller_orders'
        ]
        read_only_fields = [
            'id', 'reference', 'subtotal', 'total_amount',
            'created_at', 'updated_at'
        ]

from apps.orders.models import Order, OrderItem, SellerOrder
from apps.catalog.models import Product
from apps.accounts.models import SellerProfile


# =============================================================================
# ORDER ITEM SERIALIZERS
# =============================================================================

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items (read-only for customers)."""
    
    seller_name = serializers.CharField(source='seller.shop_name', read_only=True)
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'seller',
            'seller_name',
            'product',
            'product_id',
            'title_snapshot',
            'price_snapshot',
            'quantity',
            'line_total',
            'created_at',
        ]
        read_only_fields = fields


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items during checkout."""
    
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.select_related('seller').get(pk=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")
        
        # Check product is published
        if product.status != 'published':
            raise serializers.ValidationError(f"Product '{product.name}' is not available.")
        
        # Check seller is approved
        if product.seller.approval_status != 'approved':
            raise serializers.ValidationError(f"Seller for '{product.name}' is not approved.")
        
        return value
    
    def validate(self, attrs):
        product_id = attrs['product_id']
        quantity = attrs['quantity']
        
        product = Product.objects.get(pk=product_id)
        
        # Check stock
        if product.stock < quantity:
            raise serializers.ValidationError({
                'quantity': f"Insufficient stock. Available: {product.stock}"
            })
        
        attrs['product'] = product
        return attrs


# =============================================================================
# ORDER SERIALIZERS
# =============================================================================

class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order lists."""
    
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'reference',
            'status',
            'payment_status',
            'total_amount',
            'currency',
            'items_count',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order details including items."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'reference',
            'user',
            'user_email',
            'status',
            'payment_status',
            'subtotal',
            'tax',
            'shipping_fee',
            'discount',
            'total_amount',
            'currency',
            'coupon_code',
            'shipping_address',
            'billing_address',
            'customer_note',
            'items',
            'created_at',
            'updated_at',
            'paid_at',
        ]
        read_only_fields = fields


class ShippingAddressSerializer(serializers.Serializer):
    """Serializer for shipping address in checkout."""
    
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address1 = serializers.CharField(max_length=255)
    address2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    region = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100)


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout payload.
    
    Accepts either:
    - shipping_address_id: ID of existing Address
    - shipping_address: Full address data as JSON object
    """
    
    items = OrderItemCreateSerializer(many=True)
    
    # Option 1: Use existing address by ID
    shipping_address_id = serializers.IntegerField(required=False)
    billing_address_id = serializers.IntegerField(required=False)
    
    # Option 2: Provide address data directly
    shipping_address = ShippingAddressSerializer(required=False)
    billing_address = ShippingAddressSerializer(required=False)
    
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    customer_note = serializers.CharField(required=False, allow_blank=True)
    currency = serializers.ChoiceField(
        choices=['EUR', 'USD', 'GBP', 'XOF'],
        default='EUR'
    )
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value
    
    def validate(self, attrs):
        from apps.customers.models import Address
        
        # Validate shipping address - either ID or data must be provided
        shipping_address_id = attrs.get('shipping_address_id')
        shipping_address = attrs.get('shipping_address')
        
        if not shipping_address_id and not shipping_address:
            raise serializers.ValidationError({
                'shipping_address': 'Either shipping_address_id or shipping_address is required.'
            })
        
        # If ID provided, fetch and convert to dict
        if shipping_address_id:
            request = self.context.get('request')
            if request:
                try:
                    address = Address.objects.get(pk=shipping_address_id, user=request.user)
                    attrs['shipping_address'] = {
                        'full_name': address.full_name,
                        'phone': getattr(address, 'phone_number', ''),
                        'address1': getattr(address, 'street_address', ''),
                        'address2': getattr(address, 'building_apartment', ''),
                        'city': address.city or '',
                        'region': getattr(address, 'state_province', ''),
                        'postal_code': address.postal_code or '',
                        'country': address.country or '',
                    }
                except Address.DoesNotExist:
                    raise serializers.ValidationError({
                        'shipping_address_id': 'Address not found or does not belong to you.'
                    })
        
        # Handle billing address similarly
        billing_address_id = attrs.get('billing_address_id')
        if billing_address_id:
            request = self.context.get('request')
            if request:
                try:
                    address = Address.objects.get(pk=billing_address_id, user=request.user)
                    attrs['billing_address'] = {
                        'full_name': address.full_name,
                        'phone': getattr(address, 'phone_number', ''),
                        'address1': getattr(address, 'street_address', ''),
                        'address2': getattr(address, 'building_apartment', ''),
                        'city': address.city or '',
                        'region': getattr(address, 'state_province', ''),
                        'postal_code': address.postal_code or '',
                        'country': address.country or '',
                    }
                except Address.DoesNotExist:
                    raise serializers.ValidationError({
                        'billing_address_id': 'Address not found or does not belong to you.'
                    })
        
        return attrs


# =============================================================================
# SELLER ORDER SERIALIZERS
# =============================================================================

class SellerOrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer for seller view."""
    
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'title_snapshot',
            'price_snapshot',
            'quantity',
            'line_total',
            'created_at',
        ]
        read_only_fields = fields


class SellerOrderListSerializer(serializers.ModelSerializer):
    """Seller's view of orders (list)."""
    
    order_reference = serializers.CharField(source='order.reference', read_only=True)
    order_created_at = serializers.DateTimeField(source='order.created_at', read_only=True)
    customer_name = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SellerOrder
        fields = [
            'id',
            'order',
            'order_reference',
            'order_created_at',
            'customer_name',
            'status',
            'subtotal',
            'items_count',
            'tracking_number',
            'carrier',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_customer_name(self, obj):
        return obj.order.user.get_full_name() or obj.order.user.email
    
    def get_items_count(self, obj):
        return obj.items.count()


class SellerOrderDetailSerializer(serializers.ModelSerializer):
    """Seller's view of order details."""
    
    order_reference = serializers.CharField(source='order.reference', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)
    order_payment_status = serializers.CharField(source='order.payment_status', read_only=True)
    customer_name = serializers.SerializerMethodField()
    shipping_address = serializers.JSONField(source='order.shipping_address', read_only=True)
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = SellerOrder
        fields = [
            'id',
            'order',
            'order_reference',
            'order_status',
            'order_payment_status',
            'customer_name',
            'shipping_address',
            'status',
            'subtotal',
            'tracking_number',
            'carrier',
            'seller_note',
            'items',
            'created_at',
            'updated_at',
            'shipped_at',
            'delivered_at',
        ]
        read_only_fields = [
            'id', 'order', 'order_reference', 'order_status', 
            'order_payment_status', 'customer_name', 'shipping_address',
            'subtotal', 'items', 'created_at', 'updated_at',
            'shipped_at', 'delivered_at'
        ]
    
    def get_customer_name(self, obj):
        return obj.order.user.get_full_name() or obj.order.user.email
    
    def get_items(self, obj):
        items = obj.order.items.filter(seller=obj.seller)
        return SellerOrderItemSerializer(items, many=True).data


class SellerOrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for seller to update their order status."""
    
    class Meta:
        model = SellerOrder
        fields = [
            'status',
            'tracking_number',
            'carrier',
            'seller_note',
        ]
    
    def validate_status(self, value):
        instance = self.instance
        if not instance:
            return value
        
        # Define valid transitions
        valid_transitions = {
            'pending': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],
            'cancelled': [],
        }
        
        current_status = instance.status
        allowed = valid_transitions.get(current_status, [])
        
        if value != current_status and value not in allowed:
            raise serializers.ValidationError(
                f"Cannot transition from '{current_status}' to '{value}'. "
                f"Allowed: {allowed}"
            )
        
        return value


# =============================================================================
# ADMIN ORDER SERIALIZERS
# =============================================================================

class AdminOrderListSerializer(serializers.ModelSerializer):
    """Admin view of all orders."""
    
    customer_email = serializers.EmailField(source='user.email', read_only=True)
    customer_name = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    sellers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'reference',
            'customer_email',
            'customer_name',
            'status',
            'payment_status',
            'subtotal',
            'total_amount',
            'currency',
            'items_count',
            'sellers_count',
            'created_at',
            'paid_at',
        ]
        read_only_fields = fields
    
    def get_customer_name(self, obj):
        return obj.user.get_full_name() or obj.user.email
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def get_sellers_count(self, obj):
        return len(obj.seller_ids)


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    """Admin detailed view of an order."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    seller_orders = SellerOrderListSerializer(many=True, read_only=True)
    customer_email = serializers.EmailField(source='user.email', read_only=True)
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'reference',
            'user',
            'customer_email',
            'customer_name',
            'status',
            'payment_status',
            'subtotal',
            'tax',
            'shipping_fee',
            'discount',
            'total_amount',
            'currency',
            'coupon_code',
            'shipping_address',
            'billing_address',
            'customer_note',
            'admin_note',
            'items',
            'seller_orders',
            'created_at',
            'updated_at',
            'paid_at',
        ]
        read_only_fields = [
            'id', 'reference', 'user', 'customer_email', 'customer_name',
            'subtotal', 'total_amount', 'items', 'seller_orders',
            'created_at', 'updated_at', 'paid_at'
        ]
    
    def get_customer_name(self, obj):
        return obj.user.get_full_name() or obj.user.email


class AdminOrderUpdateSerializer(serializers.ModelSerializer):
    """Admin can update order status and notes."""
    
    class Meta:
        model = Order
        fields = [
            'status',
            'payment_status',
            'admin_note',
        ]
