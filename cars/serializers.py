from decimal import Decimal

from rest_framework import serializers
from .models import Car, CarPayment


class CarSerializer(serializers.ModelSerializer):
    """Full representation, including unique_price and is_postpaid — admin use only."""

    class Meta:
        model = Car
        fields = ['id', 'plate_number', 'owner_name', 'phone_number', 'unique_price', 'is_postpaid', 'optional_info', 'created_at']
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


class CarPaymentSerializer(serializers.ModelSerializer):
    """A recorded settlement event for a car."""
    recorded_by_name = serializers.CharField(source='recorded_by.name', read_only=True, default=None)

    class Meta:
        model = CarPayment
        fields = ['id', 'car', 'amount', 'recorded_by_name', 'paid_at', 'note', 'created_at']
        read_only_fields = fields


class CarPaymentInputSerializer(serializers.Serializer):
    """Request body for recording a payment against a car's balance."""
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    note = serializers.CharField(required=False, allow_blank=True, default='')