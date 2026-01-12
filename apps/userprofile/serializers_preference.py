from rest_framework import serializers
from .models_preference import UserPreference

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['id', 'user', 'language', 'notifications_enabled']
        read_only_fields = ['id', 'user']
