from rest_framework import serializers
from .models import DashboardStat

class DashboardStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardStat
        fields = ['id', 'user', 'stat_type', 'value', 'period', 'created_at']
        read_only_fields = ['id', 'created_at', 'user']
