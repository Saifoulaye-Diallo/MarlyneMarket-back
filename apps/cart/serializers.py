from rest_framework import serializers
from .models import CartItem

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'user', 'product', 'quantity', 'date_added']
        read_only_fields = ['id', 'date_added', 'user']
