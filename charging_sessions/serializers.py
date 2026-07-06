from rest_framework import serializers
from charging_sessions.models import ChargingSession
from cars.serializers import CarSerializer
from chargers.models import Charger
from chargers.serializers import ChargerSerializer


class ChargingSessionSerializer(serializers.ModelSerializer):
    car_plate = serializers.CharField(source='car.plate_number', read_only=True)
    charger_name = serializers.CharField(source='charger.name', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)
    duration = serializers.DurationField(read_only=True)

    class Meta:
        model = ChargingSession
        fields = [
            'id', 'station', 'station_name', 'charger', 'charger_name', 'port',
            'staff', 'shift', 'car', 'car_plate',
            'starting_car_percentage', 'ending_car_percentage',
            'watt_consumed', 'total_price', 'duration',
            'started_at', 'ended_at'
        ]
        read_only_fields = ['total_price', 'started_at', 'ended_at', 'station', 'staff', 'shift']


class StartSessionSerializer(serializers.Serializer):
    charger_id = serializers.IntegerField()
    port = serializers.ChoiceField(choices=Charger.PORT_CHOICES)
    plate_number = serializers.CharField(max_length=50)
    starting_car_percentage = serializers.IntegerField(min_value=0, max_value=100)


class EndSessionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    watt_consumed = serializers.DecimalField(max_digits=12, decimal_places=2)
    ending_car_percentage = serializers.IntegerField(min_value=0, max_value=100)