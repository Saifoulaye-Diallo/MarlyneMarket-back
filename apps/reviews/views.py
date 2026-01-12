"""
Views for reviews app.
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.reviews.models import Review, ReviewHelpful
from apps.reviews.serializers import (
    ReviewSerializer,
    CreateReviewSerializer,
    UpdateReviewSerializer,
    AdminReviewSerializer,
    ModerateReviewSerializer,
    ReviewHelpfulSerializer,
)
from apps.reviews.permissions import IsReviewOwner
from apps.orders.permissions import IsSuperAdmin


class PublicReviewViewSet(viewsets.ModelViewSet):
    """
    Public product reviews - now supports creating reviews.
    
    list: GET /api/reviews/?product={id}
    create: POST /api/reviews/
    retrieve: GET /api/reviews/{id}/
    """
    serializer_class = ReviewSerializer
    lookup_value_regex = r"\d+"
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['product', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Set permissions based on action.
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        if self.action == 'create':
            # For creation, don't filter
            return Review.objects.all()
        return Review.objects.filter(
            status='approved'
        ).select_related('user', 'product')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateReviewSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """Set the current user as the review author."""
        serializer.save(user=self.request.user)


class CustomerReviewViewSet(viewsets.ModelViewSet):
    """
    Customer review management.
    
    list: GET /api/reviews/my/
    create: POST /api/reviews/my/
    retrieve: GET /api/reviews/my/{id}/
    update: PUT/PATCH /api/reviews/my/{id}/
    destroy: DELETE /api/reviews/my/{id}/
    """
    permission_classes = [IsAuthenticated, IsReviewOwner]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        return Review.objects.filter(
            user=self.request.user
        ).select_related('product')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateReviewSerializer
        if self.action in ['update', 'partial_update']:
            return UpdateReviewSerializer
        return ReviewSerializer


class AdminReviewViewSet(viewsets.ModelViewSet):
    """
    Admin review management and moderation.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'is_verified_purchase', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        return Review.objects.all().select_related(
            'user', 'product', 'moderated_by'
        )
    
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return ModerateReviewSerializer
        return AdminReviewSerializer
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve a review."""
        obj = self.get_object()
        obj.status = 'approved'
        obj.moderated_by = request.user
        obj.save()
        return Response(AdminReviewSerializer(obj).data)
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject a review."""
        obj = self.get_object()
        obj.status = 'rejected'
        obj.moderated_by = request.user
        obj.moderation_note = request.data.get('moderation_note', '')
        obj.save()
        return Response(AdminReviewSerializer(obj).data)


class ReviewHelpfulView(generics.CreateAPIView):
    """
    Vote on review helpfulness.
    
    POST /api/reviews/{id}/helpful/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewHelpfulSerializer
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['review'] = self.kwargs.get('review_id')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
