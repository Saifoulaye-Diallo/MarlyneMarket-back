"""
Views for orders app.
Provides endpoints for customers, sellers, and admins.
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from apps.orders.models import Order, OrderItem, SellerOrder
from apps.orders.serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    CheckoutSerializer,
    SellerOrderListSerializer,
    SellerOrderDetailSerializer,
    SellerOrderUpdateSerializer,
    AdminOrderListSerializer,
    AdminOrderDetailSerializer,
    AdminOrderUpdateSerializer,
)
from apps.orders.permissions import (
    IsCustomer,
    IsSeller,
    IsSellerActive,
    IsSuperAdmin,
    IsOrderOwner,
    IsSellerOrderOwner,
    CanCreateOrder,
)
from apps.orders.services.checkout import create_order_from_cart


# =============================================================================
# CUSTOMER VIEWS
# =============================================================================

class CustomerOrderViewSet(viewsets.ModelViewSet):
    """
    Customer order management.
    
    list: GET /api/orders/
    retrieve: GET /api/orders/{id}/
    checkout: POST /api/orders/checkout/
    update: PATCH /api/orders/{id}/ (restricted to order owner or admin)
    """
    
    permission_classes = [IsAuthenticated, IsOrderOwner]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'payment_status']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return orders for permission checks."""
        if not self.request.user.is_authenticated:
            return Order.objects.none()
        
        # For list and retrieve, return only user's orders (404 if not found)
        if self.action in ['list', 'retrieve']:
            return Order.objects.filter(user=self.request.user).prefetch_related('items')
        
        # For update actions, return all orders for proper 403 vs 404 handling
        # (sellers trying to modify customer orders should get 403, not 404)
        if self.action in ['update', 'partial_update']:
            return Order.objects.all().prefetch_related('items')
            
        # Default: user's orders
        return Order.objects.filter(user=self.request.user).prefetch_related('items')
    
    def get_permissions(self):
        """Different permissions for different actions."""
        if self.action in ['create', 'destroy']:
            # Forbid create/delete via this endpoint
            return [IsAuthenticated()]  # Will be further restricted in the methods
        elif self.action in ['update', 'partial_update']:
            # Only admins can update orders directly (customers can't)
            from apps.accounts.permissions import IsSuperAdmin
            return [IsAuthenticated(), IsSuperAdmin()]
        else:
            # List, retrieve, checkout
            return [IsAuthenticated(), IsOrderOwner()]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, CanCreateOrder])
    def checkout(self, request):
        """
        Create a new order from cart items.
        
        POST /api/orders/checkout/
        
        Payload (Option 1 - with address ID):
        {
            "items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 3, "quantity": 1}
            ],
            "shipping_address_id": 5,
            "currency": "EUR",
            "customer_note": "Please deliver in the morning"
        }
        
        Payload (Option 2 - with full address):
        {
            "items": [
                {"product_id": 1, "quantity": 2}
            ],
            "shipping_address": {
                "full_name": "John Doe",
                "phone": "+33612345678",
                "address1": "123 Rue Example",
                "city": "Paris",
                "postal_code": "75001",
                "country": "France"
            }
        }
        """
        serializer = CheckoutSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        result = create_order_from_cart(serializer.validated_data, request.user)
        
        if 'errors' in result:
            return Response(
                {'errors': result['errors']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order = result['order']
        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED
        )
    
    def create(self, request, *args, **kwargs):
        """Disable direct order creation - use checkout instead."""
        return Response(
            {'detail': 'Use /api/orders/checkout/ to create orders'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Disable order deletion."""
        return Response(
            {'detail': 'Order deletion is not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, *args, **kwargs):
        """Allow limited order updates by owner or admin."""
        # IsOrderOwner will handle the permission check
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Allow limited order updates by owner or admin."""
        # IsOrderOwner will handle the permission check
        return super().partial_update(request, *args, **kwargs)


# =============================================================================
# SELLER VIEWS
# =============================================================================

class SellerOrderViewSet(viewsets.ModelViewSet):
    """
    Seller order management.
    
    Sellers can only see and manage orders containing their products.
    
    list: GET /api/orders/seller/
    retrieve: GET /api/orders/seller/{id}/
    update_status: PATCH /api/orders/seller/{id}/status/
    """
    
    permission_classes = [IsAuthenticated, IsSeller, IsSellerOrderOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['order__reference']
    ordering_fields = ['created_at', 'subtotal', 'updated_at']
    ordering = ['-created_at']
    http_method_names = ['get', 'patch', 'head', 'options']
    
    def get_queryset(self):
        """Return seller's orders with appropriate filtering."""
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'seller_profile'):
            return SellerOrder.objects.none()
        
        # For list and retrieve, show only seller's orders (404 if not found)
        if self.action in ['list', 'retrieve']:
            return SellerOrder.objects.filter(
                seller=user.seller_profile
            ).select_related('order', 'seller').prefetch_related('order__items')
        
        # For update actions, show all SellerOrders for proper 403 vs 404 handling
        if self.action in ['update', 'partial_update', 'update_status']:
            return SellerOrder.objects.all().select_related('order', 'seller').prefetch_related('order__items')
            
        # Default: seller's orders
        return SellerOrder.objects.filter(
            seller=user.seller_profile
        ).select_related('order', 'seller').prefetch_related('order__items')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SellerOrderDetailSerializer
        if self.action in ['partial_update', 'update_status']:
            return SellerOrderUpdateSerializer
        return SellerOrderListSerializer
    
    def partial_update(self, request, *args, **kwargs):
        """Update seller order status and tracking info."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Handle status transitions
        new_status = serializer.validated_data.get('status')
        if new_status == 'shipped' and instance.status != 'shipped':
            instance.shipped_at = timezone.now()
        elif new_status == 'delivered' and instance.status != 'delivered':
            instance.delivered_at = timezone.now()
        
        serializer.save()
        
        return Response(SellerOrderDetailSerializer(instance).data)
    
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Update seller order status.
        
        PATCH /api/orders/seller/{id}/status/
        
        Payload:
        {
            "status": "shipped",
            "tracking_number": "1Z999AA10123456784",
            "carrier": "UPS"
        }
        """
        return self.partial_update(request)


# =============================================================================
# ADMIN VIEWS
# =============================================================================

class AdminOrderViewSet(viewsets.ModelViewSet):
    """
    Admin order management.
    
    Full access to all orders.
    
    list: GET /api/orders/admin/
    retrieve: GET /api/orders/admin/{id}/
    update: PATCH /api/orders/admin/{id}/
    """
    
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'currency']
    search_fields = ['reference', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'total_amount', 'paid_at']
    ordering = ['-created_at']
    http_method_names = ['get', 'patch', 'head', 'options']
    
    def get_queryset(self):
        return Order.objects.all().select_related('user').prefetch_related(
            'items', 'items__seller', 'seller_orders'
        )
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminOrderDetailSerializer
        if self.action == 'partial_update':
            return AdminOrderUpdateSerializer
        return AdminOrderListSerializer
    
    def partial_update(self, request, *args, **kwargs):
        """Admin can update order status, payment status, and notes."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Handle payment status changes
        new_payment_status = serializer.validated_data.get('payment_status')
        if new_payment_status == 'paid' and instance.payment_status != 'paid':
            instance.paid_at = timezone.now()
            # Also update order status if it was pending
            if instance.status == 'pending':
                instance.status = 'paid'
        
        serializer.save()
        
        return Response(AdminOrderDetailSerializer(instance).data)
    
    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        """
        Mark an order as paid (for manual payment confirmation).
        
        POST /api/orders/admin/{id}/mark-paid/
        """
        order = self.get_object()
        
        if order.payment_status == 'paid':
            return Response(
                {'detail': 'Order is already marked as paid.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.payment_status = 'paid'
        order.paid_at = timezone.now()
        if order.status == 'pending':
            order.status = 'paid'
        order.save()
        
        # Update all seller orders to processing
        order.seller_orders.filter(status='pending').update(status='processing')
        
        return Response(AdminOrderDetailSerializer(order).data)
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_order(self, request, pk=None):
        """
        Cancel an order and restore stock.
        
        POST /api/orders/admin/{id}/cancel/
        """
        order = self.get_object()
        
        if order.status in ['delivered', 'refunded']:
            return Response(
                {'detail': f'Cannot cancel order with status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restore stock
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save(update_fields=['stock'])
        
        order.status = 'cancelled'
        order.save()
        
        # Update all seller orders
        order.seller_orders.update(status='cancelled')
        
        return Response(AdminOrderDetailSerializer(order).data)

# =============================================================================
# SELLER VIEWS FOR /api/seller/
# =============================================================================

class SellerOrderListView(generics.ListAPIView):
    """Seller view for their own orders."""
    permission_classes = [IsAuthenticated, IsSellerActive]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    serializer_class = SellerOrderListSerializer
    
    def get_queryset(self):
        """Return seller's orders."""
        if not hasattr(self.request.user, 'seller_profile'):
            return SellerOrder.objects.none()
        return SellerOrder.objects.filter(
            seller=self.request.user.seller_profile
        ).select_related('order', 'seller')


class SellerOrderItemListView(generics.ListAPIView):
    """Seller view for their own order items."""
    permission_classes = [IsAuthenticated, IsSellerActive]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return seller's order items."""
        if not hasattr(self.request.user, 'seller_profile'):
            return OrderItem.objects.none()
        return OrderItem.objects.filter(
            seller=self.request.user.seller_profile
        ).select_related('order', 'product', 'seller')
    
    def get_serializer_class(self):
        from apps.orders.serializers import OrderItemSerializer
        return OrderItemSerializer


class SellerOrderItemDetailView(generics.RetrieveAPIView):
    """Seller view for their order items (read-only)."""
    permission_classes = [IsAuthenticated, IsSellerActive]
    
    def get_serializer_class(self):
        from apps.orders.serializers import SellerOrderItemSerializer
        return SellerOrderItemSerializer
    
    lookup_field = 'id'
    
    def get_queryset(self):
        """Return seller's order items."""
        if not hasattr(self.request.user, 'seller_profile'):
            return OrderItem.objects.none()
        return OrderItem.objects.filter(
            seller=self.request.user.seller_profile
        ).select_related('product', 'seller', 'order')
    
    def get_object(self):
        """Override to return 403 for items not owned by the seller."""
        obj_id = self.kwargs['id']
        
        # Check if the item exists
        try:
            item = OrderItem.objects.get(id=obj_id)
        except OrderItem.DoesNotExist:
            from django.http import Http404
            raise Http404("Order item not found.")
        
        # Check if the seller owns this item
        if hasattr(self.request.user, 'seller_profile') and item.seller == self.request.user.seller_profile:
            return item
        else:
            # Item exists but seller doesn't own it - return 403
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to access this order item.")


class SellerAnalyticsView(generics.GenericAPIView):
    """Seller analytics dashboard."""
    permission_classes = [IsAuthenticated, IsSellerActive]
    
    def get(self, request):
        """Get seller's analytics."""
        if not hasattr(request.user, 'seller_profile'):
            return Response(
                {'detail': 'Seller profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        seller = request.user.seller_profile
        
        # Calculate analytics
        total_orders = SellerOrder.objects.filter(seller=seller).count()
        total_revenue = sum([
            so.order.total_amount for so in SellerOrder.objects.filter(seller=seller)
        ])
        
        return Response({
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'seller_id': seller.id,
        }, status=status.HTTP_200_OK)