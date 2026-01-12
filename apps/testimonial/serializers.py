from rest_framework import serializers
from .models import Testimonial

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'user', 'product', 'content', 'rating', 'date_created', 'is_approved']
        read_only_fields = ['id', 'date_created', 'user', 'is_approved']
