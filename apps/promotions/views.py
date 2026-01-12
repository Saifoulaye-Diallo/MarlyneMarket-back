"""
Views for promotions app.
"""
from rest_framework import viewsets, status, generics, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from decimal import Decimal

from apps.promotions.models import Coupon, CouponUsage
from apps.promotions.serializers import (
    CouponSerializer,
    ValidateCouponSerializer,
    CouponResponseSerializer,
    AdminCouponSerializer,
    SellerCouponSerializer,
    CouponUsageSerializer,
)
from apps.promotions.services import CouponService
from apps.orders.permissions import IsSeller, IsSuperAdmin


class ValidateCouponView(generics.GenericAPIView):
    """
    Validate a coupon code.
    
    POST /api/promotions/validate/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ValidateCouponSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as exc:
            # Coupon does not exist or invalid input: return 400
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        coupon = serializer.validated_data['coupon']
        cart_total = serializer.validated_data.get('cart_total', Decimal('0'))
        # Calculate estimated discount
        estimated_discount = CouponService.calculate_discount(coupon, cart_total)
        response_data = {
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': coupon.discount_value,
            'estimated_discount': estimated_discount,
            'min_purchase_amount': coupon.min_purchase_amount,
        }
        return Response(CouponResponseSerializer(response_data).data)


class ValidateCouponAltView(generics.GenericAPIView):
    """
    Alternative validate endpoint with 404 for non-existent coupons.
    
    POST /api/coupons/validate/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ValidateCouponSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as exc:
            if 'code' in exc.detail and any('does not exist' in str(e) for e in exc.detail['code']):
                return Response({'code': exc.detail['code']}, status=status.HTTP_404_NOT_FOUND)
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        coupon = serializer.validated_data['coupon']
        cart_total = serializer.validated_data.get('cart_total', Decimal('0'))
        estimated_discount = CouponService.calculate_discount(coupon, cart_total)
        response_data = {
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': coupon.discount_value,
            'estimated_discount': estimated_discount,
            'min_purchase_amount': coupon.min_purchase_amount,
        }
        return Response(CouponResponseSerializer(response_data).data)


class PublicCouponListView(generics.ListAPIView):
    """
    List active public coupons.
    
    GET /api/promotions/
    """
    permission_classes = [AllowAny]
    serializer_class = CouponSerializer
    
    def get_queryset(self):
        now = timezone.now()
        return Coupon.objects.filter(
            is_active=True,
            scope='global',
            start_date__lte=now,
            end_date__gte=now
        )


class SellerCouponViewSet(viewsets.ModelViewSet):
    """
    Seller coupon management.
    
    Sellers can only create coupons for their own products.
    """
    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = SellerCouponSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    
    def get_queryset(self):
        if not hasattr(self.request.user, 'seller_profile'):
            return Coupon.objects.none()
        return Coupon.objects.filter(
            seller=self.request.user.seller_profile
        )
    
    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """Toggle coupon active status."""
        coupon = self.get_object()
        coupon.is_active = not coupon.is_active
        coupon.save(update_fields=['is_active'])
        return Response(SellerCouponSerializer(coupon).data)


class AdminCouponViewSet(viewsets.ModelViewSet):
    """
    Admin coupon management.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = AdminCouponSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'scope', 'discount_type']
    
    def get_queryset(self):
        return Coupon.objects.all().select_related(
            'seller', 'created_by'
        ).prefetch_related('categories')
    
    @action(detail=True, methods=['get'], url_path='usages')
    def usages(self, request, pk=None):
        """Get coupon usage history."""
        coupon = self.get_object()
        usages = CouponUsage.objects.filter(
            coupon=coupon
        ).select_related('user', 'order')
        serializer = CouponUsageSerializer(usages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """Toggle coupon active status."""
        coupon = self.get_object()
        coupon.is_active = not coupon.is_active
        coupon.save(update_fields=['is_active'])
        return Response(AdminCouponSerializer(coupon).data)
