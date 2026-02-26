from rest_framework import serializers
from .models import Car


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = ['id', 'plate_number', 'optional_info', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_plate_number(self, value):
        return value.upper().strip()


class CarSearchSerializer(serializers.Serializer):
    plate_number = serializers.CharField()

    def validate_plate_number(self, value):
        return value.upper().strip()