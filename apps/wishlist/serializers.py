from rest_framework import serializers
from .models import WishlistItem

class WishlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['id', 'user', 'product', 'date_added']
        read_only_fields = ['id', 'date_added', 'user']
