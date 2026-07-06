from rest_framework import serializers
from .models import Car


class CarSerializer(serializers.ModelSerializer):
    """Full representation, including unique_price — admin use only."""

    class Meta:
        model = Car
        fields = ['id', 'plate_number', 'owner_name', 'phone_number', 'unique_price', 'optional_info', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_plate_number(self, value):
        return value.upper().strip()


class CarRegisterSerializer(serializers.ModelSerializer):
    """Staff-facing representation — unique_price is admin-only and excluded here."""

    class Meta:
        model = Car
        fields = ['id', 'plate_number', 'owner_name', 'phone_number', 'optional_info', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_plate_number(self, value):
        return value.upper().strip()


class CarSearchSerializer(serializers.Serializer):
    plate_number = serializers.CharField()

    def validate_plate_number(self, value):
        return value.upper().strip()