from rest_framework import serializers
from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'station', 'station_name', 'description',
            'amount_vat_exclusive', 'input_vat', 'date',
        ]
        read_only_fields = ['id', 'date']
