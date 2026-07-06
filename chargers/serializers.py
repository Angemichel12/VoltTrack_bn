from decimal import Decimal
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Charger, ShiftRecord
from django.utils import timezone


class ChargerPortSerializer(serializers.Serializer):
    port = serializers.ChoiceField(choices=Charger.PORT_CHOICES)
    available = serializers.BooleanField()


class ChargerSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)
    ports = serializers.SerializerMethodField()

    class Meta:
        model = Charger
        fields = ['id', 'name', 'station', 'station_name', 'ports', 'created_at']
        read_only_fields = ['created_at']

    @extend_schema_field(ChargerPortSerializer(many=True))
    def get_ports(self, obj):
        occupied = set(obj.sessions.filter(ended_at__isnull=True).values_list('port', flat=True))
        return [
            {'port': port, 'available': port not in occupied}
            for port in Charger.PORTS
        ]


class ShiftRecordSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = ShiftRecord
        fields = [
            'id', 'station', 'station_name',
            'staff', 'staff_name',
            'shift_start', 'shift_end',
            'start_kwatts_in_cashpower', 'addition_kwatt_in_cashpower', 'total_kwatt',
            'total_earned_money_on_shift', 'total_kwatt_used_on_shift', 'total_car_charged',
            'money_on_momo', 'end_kwatts_in_cashpower',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'staff', 'total_kwatt', 'total_earned_money_on_shift', 'total_kwatt_used_on_shift',
            'total_car_charged', 'money_on_momo', 'end_kwatts_in_cashpower', 'created_at', 'updated_at',
        ]


class OpenShiftSerializer(serializers.ModelSerializer):
    shift_start = serializers.DateTimeField(
        default=timezone.now,
        required=False
    )

    class Meta:
        model = ShiftRecord
        fields = ['id', 'station', 'shift_start', 'start_kwatts_in_cashpower', 'notes']


class AddCashpowerSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))


class CloseShiftSerializer(serializers.Serializer):
    money_on_momo = serializers.DecimalField(max_digits=12, decimal_places=2)
    end_kwatts_in_cashpower = serializers.DecimalField(max_digits=10, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)