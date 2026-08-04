from rest_framework import serializers
from charging_sessions.models import ChargingSession
from chargers.models import ShiftRecord
from expenses.models import Expense


class SessionReportSerializer(serializers.ModelSerializer):
    shift_id = serializers.IntegerField(source='shift.id', read_only=True)
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)
    charger_name = serializers.CharField(source='charger.name', read_only=True)
    car_plate = serializers.CharField(source='car.plate_number', read_only=True)
    duration = serializers.DurationField(read_only=True)

    class Meta:
        model = ChargingSession
        fields = [
            'id', 'shift_id', 'staff_name', 'station_name', 'charger_name', 'port',
            'car_plate', 'starting_car_percentage', 'ending_car_percentage',
            'watt_consumed', 'is_estimated', 'duration', 'total_price', 'started_at', 'ended_at',
        ]


class ShiftReportSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = ShiftRecord
        fields = [
            'id', 'staff_name', 'station_name', 'shift_start',
            'start_kwatts_in_cashpower', 'addition_kwatt_in_cashpower', 'total_kwatt',
            'total_earned_money_on_shift', 'total_kwatt_used_on_shift',
            'money_on_momo', 'end_kwatts_in_cashpower',
            'shift_end', 'total_car_charged',
        ]


class ExpenseReportSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'station_name', 'description',
            'amount_vat_exclusive', 'input_vat', 'date',
        ]
