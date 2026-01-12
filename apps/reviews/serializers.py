"""
Serializers for reviews app.
"""
from rest_framework import serializers
from .models import Review, ReviewHelpful
from apps.orders.models import OrderItem


class ReviewHelpfulSerializer(serializers.ModelSerializer):
    """Serializer for review helpful votes"""
    
    class Meta:
        model = ReviewHelpful
        fields = ['id', 'review', 'user', 'vote_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for product reviews with approval workflow"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    helpful_votes = ReviewHelpfulSerializer(
        many=True,
        read_only=True
    )
    
    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name', 'user', 'user_name', 'rating',
            'title', 'comment', 'status', 'is_verified_purchase', 'helpful_count',
            'unhelpful_count', 'seller_response', 'moderated_at',
            'order_reference', 'created_at', 'updated_at', 'helpful_votes'
        ]
        read_only_fields = [
            'id', 'status', 'moderated_at', 'helpful_count', 'unhelpful_count',
            'created_at', 'updated_at'
        ]


class CreateReviewSerializer(serializers.ModelSerializer):
    """Create review serializer."""
    
    order_item = serializers.PrimaryKeyRelatedField(
        queryset=OrderItem.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Review
        fields = ['product', 'order_item', 'rating', 'title', 'comment']
    
    def validate(self, attrs):
        user = self.context['request'].user
        product = attrs.get('product')
        order_item = attrs.get('order_item')
        
        # Check for duplicate review
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError(
                "You have already reviewed this product."
            )
        
        # If order_item provided, verify ownership and delivery
        if order_item is not None:
            if order_item.order.user != user:
                raise serializers.ValidationError(
                    "This order item does not belong to you."
                )
            if order_item.product != product:
                raise serializers.ValidationError(
                    "Order item product must match review product."
                )
            if order_item.order.status != 'delivered':
                raise serializers.ValidationError(
                    "You can only review products from delivered orders."
                )
        
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        order_item = validated_data.pop('order_item', None)
        
        validated_data['user'] = user
        # Mark verified purchase only when order_item is provided
        if order_item is not None:
            validated_data['is_verified_purchase'] = True
            validated_data['order_reference'] = order_item.order.reference
        
        return super().create(validated_data)


class UpdateReviewSerializer(serializers.ModelSerializer):
    """Update own review serializer."""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']


class AdminReviewSerializer(serializers.ModelSerializer):
    """Admin review serializer with full details."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)
    moderated_by_email = serializers.EmailField(
        source='moderated_by.email', 
        read_only=True
    )
    
    class Meta:
        model = Review
        fields = [
            'id',
            'user',
            'user_email',
            'product',
            'product_title',
            'rating',
            'title',
            'comment',
            'status',
            'is_verified_purchase',
            'moderated_by',
            'moderated_by_email',
            'moderation_note',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'product', 'is_verified_purchase', 'created_at', 'updated_at']


class ModerateReviewSerializer(serializers.ModelSerializer):
    """Moderate review serializer."""
    
    class Meta:
        model = Review
        fields = ['is_approved', 'moderation_note']
    
    def update(self, instance, validated_data):
        instance.moderated_by = self.context['request'].user
        return super().update(instance, validated_data)


class ReviewHelpfulSerializer(serializers.ModelSerializer):
    """Review helpful vote serializer."""
    
    class Meta:
        model = ReviewHelpful
        fields = ['review', 'is_helpful']
    
    def create(self, validated_data):
        user = self.context['request'].user
        review = validated_data['review']
        
        vote, created = ReviewHelpful.objects.update_or_create(
            user=user,
            review=review,
            defaults={'is_helpful': validated_data.get('is_helpful', True)}
        )
        return vote
