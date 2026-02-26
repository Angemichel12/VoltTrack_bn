from rest_framework import serializers
from .models import Charger, ShiftRecord


class ChargerSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = Charger
        fields = ['id', 'name', 'station', 'station_name', 'created_at']
        read_only_fields = ['created_at']


class ShiftRecordSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = ShiftRecord
        fields = [
            'id', 'station', 'station_name',
            'staff', 'staff_name',
            'shift_start', 'shift_end',
            'kwh_start', 'kwh_end', 'kwh_consumed',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['kwh_consumed', 'staff', 'created_at', 'updated_at']

    def validate(self, attrs):
        kwh_start = attrs.get('kwh_start', getattr(self.instance, 'kwh_start', None))
        kwh_end = attrs.get('kwh_end')
        if kwh_end is not None and kwh_end <= kwh_start:
            raise serializers.ValidationError("kwh_end must be greater than kwh_start.")
        return attrs


class OpenShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftRecord
        fields = ['id', 'station', 'shift_start', 'kwh_start', 'notes']


class CloseShiftSerializer(serializers.Serializer):
    kwh_end = serializers.DecimalField(max_digits=10, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)