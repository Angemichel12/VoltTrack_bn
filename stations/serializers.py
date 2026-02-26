from rest_framework import serializers
from .models import Station


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ['id', 'name', 'price_per_watt', 'created_at']
        read_only_fields = ['created_at']