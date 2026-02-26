from rest_framework import serializers
from charging_sessions.models import ChargingSession
from cars.serializers import CarSerializer
from chargers.serializers import ChargerSerializer


class ChargingSessionSerializer(serializers.ModelSerializer):
    car_plate = serializers.CharField(source='car.plate_number', read_only=True)
    charger_name = serializers.CharField(source='charger.name', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = ChargingSession
        fields = [
            'id', 'station', 'station_name', 'charger', 'charger_name',
            'staff', 'car', 'car_plate', 'watt_consumed', 'total_price',
            'started_at', 'ended_at'
        ]
        read_only_fields = ['total_price', 'started_at', 'ended_at', 'station', 'staff']


class StartSessionSerializer(serializers.Serializer):
    charger_id = serializers.IntegerField()
    plate_number = serializers.CharField(max_length=50)


class EndSessionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    watt_consumed = serializers.DecimalField(max_digits=12, decimal_places=2)