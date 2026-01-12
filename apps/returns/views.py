"""
Views for returns app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.returns.models import ReturnRequest
from apps.returns.serializers import (
    ReturnRequestSerializer,
    CreateReturnRequestSerializer,
    UpdateReturnRequestSerializer,
)
from apps.returns.permissions import IsReturnOwner, IsReturnSeller
from apps.orders.permissions import IsSeller, IsSuperAdmin


class CustomerReturnViewSet(viewsets.ModelViewSet):
    """
    Customer return request management.
    
    list: GET /api/returns/
    create: POST /api/returns/
    retrieve: GET /api/returns/{id}/
    update: PATCH /api/returns/{id}/ (restricted)
    """
    permission_classes = [IsAuthenticated, IsReturnOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    lookup_value_regex = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    
    def get_queryset(self):
        return ReturnRequest.objects.filter(
            user=self.request.user
        ).select_related('order_item', 'order_item__order', 'order_item__seller')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateReturnRequestSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateReturnRequestSerializer
        return ReturnRequestSerializer
    
    def update(self, request, *args, **kwargs):
        """Customers can only update limited fields."""
        instance = self.get_object()
        
        # Customers cannot change status - only sellers/admins can
        if 'status' in request.data and not request.user.is_superuser:
            return Response(
                {'detail': 'You do not have permission to change return status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Customers can only update limited fields."""
        return self.update(request, *args, **kwargs)


class SellerReturnViewSet(viewsets.ModelViewSet):
    """
    Seller return request management.
    
    list: GET /api/returns/seller/
    update: PATCH /api/returns/seller/{id}/
    """
    permission_classes = [IsAuthenticated, IsSeller, IsReturnSeller]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    lookup_value_regex = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    
    def get_queryset(self):
        if not hasattr(self.request.user, 'seller_profile'):
            return ReturnRequest.objects.none()
        return ReturnRequest.objects.filter(
            order_item__seller=self.request.user.seller_profile
        ).select_related('order_item', 'order_item__order', 'user')
    
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UpdateReturnRequestSerializer
        return ReturnRequestSerializer
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve a return request."""
        obj = self.get_object()
        if obj.status not in ['requested', 'initiated']:
            return Response(
                {'error': 'Can only approve requested returns'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UpdateReturnRequestSerializer(
            obj,
            data={'status': 'approved'},
            context={'request': request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReturnRequestSerializer(obj).data)
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject a return request."""
        obj = self.get_object()
        if obj.status not in ['requested', 'initiated']:
            return Response(
                {'error': 'Can only reject requested returns'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UpdateReturnRequestSerializer(
            obj,
            data={
                'status': 'rejected',
                'response_note': request.data.get('response_note', '')
            },
            context={'request': request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReturnRequestSerializer(obj).data)


class AdminReturnViewSet(viewsets.ModelViewSet):
    """
    Admin return request management.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'reason']
    http_method_names = ['get', 'patch', 'head', 'options']
    
    def get_queryset(self):
        return ReturnRequest.objects.all().select_related(
            'order_item', 'order_item__order', 'order_item__seller', 'user'
        )
    
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UpdateReturnRequestSerializer
        return ReturnRequestSerializer
    
    @action(detail=True, methods=['post'], url_path='mark-refunded')
    def mark_refunded(self, request, pk=None):
        """Mark a return as refunded."""
        obj = self.get_object()
        if obj.status not in ['approved', 'received']:
            return Response(
                {'error': 'Can only refund approved/received returns'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UpdateReturnRequestSerializer(
            obj,
            data={'status': 'refunded'},
            context={'request': request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReturnRequestSerializer(obj).data)
