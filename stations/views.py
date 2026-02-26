from rest_framework.views import APIView
from django.db.models import Sum, Count

from .models import Station
from .serializers import StationSerializer
from chargers.models import Charger, ShiftRecord
from chargers.serializers import ChargerSerializer, ShiftRecordSerializer
from charging_sessions.models import ChargingSession
from charging_sessions.serializers import ChargingSessionSerializer
from users.permissions import IsAdmin, IsStaff
from users.exceptions import success_response, error_response


# ── Admin ────────────────────────────────────────────────────────────────────

class AdminStationListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        stations = Station.objects.all()
        return success_response(data=StationSerializer(stations, many=True).data)

    def post(self, request):
        serializer = StationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Station created", status_code=201)


class AdminStationDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        from django.shortcuts import get_object_or_404
        station = get_object_or_404(Station, pk=pk)
        serializer = StationSerializer(station, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Station updated")

    def delete(self, request, pk):
        from django.shortcuts import get_object_or_404
        station = get_object_or_404(Station, pk=pk)
        station.delete()
        return success_response(message="Station deleted")


class AdminReportsView(APIView):
    """Admin-level report across all stations."""
    permission_classes = [IsAdmin]

    def get(self, request):
        sessions_qs = ChargingSession.objects.all()
        summary = sessions_qs.aggregate(
            total_earnings=Sum('total_price'),
            total_watt=Sum('watt_consumed'),
            total_sessions=Count('id')
        )
        per_station = sessions_qs.values('station__id', 'station__name').annotate(
            sessions=Count('id'),
            earnings=Sum('total_price'),
            watt_used=Sum('watt_consumed')
        )
        return success_response(data={
            'summary': summary,
            'per_station': list(per_station)
        })


# ── Staff ────────────────────────────────────────────────────────────────────

class StaffDashboardView(APIView):
    """Staff sees their own station summary."""
    permission_classes = [IsStaff]

    def get(self, request):
        if not request.user.station:
            return error_response(message="You are not assigned to any station", status_code=404)

        station = request.user.station
        charger_count = Charger.objects.filter(station=station).count()
        session_stats = ChargingSession.objects.filter(station=station).aggregate(
            total_sessions=Count('id'),
            total_earnings=Sum('total_price'),
            total_watt=Sum('watt_consumed')
        )
        open_shift = ShiftRecord.objects.filter(
            station=station, staff=request.user, shift_end__isnull=True
        ).first()

        return success_response(data={
            'station': StationSerializer(station).data,
            'charger_count': charger_count,
            'open_shift': ShiftRecordSerializer(open_shift).data if open_shift else None,
            **session_stats
        })


class SetPriceView(APIView):
    """Admin sets price per watt for a station."""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        station = get_object_or_404(Station, pk=pk)
        price = request.data.get('price_per_watt')
        if price is None:
            return error_response(message="price_per_watt is required")
        station.price_per_watt = price
        station.save(update_fields=['price_per_watt'])
        return success_response(data=StationSerializer(station).data, message="Price updated")


class StaffReportsView(APIView):
    """Staff sees reports for their own station."""
    permission_classes = [IsStaff]

    def get(self, request):
        if not request.user.station:
            return error_response(message="You are not assigned to any station", status_code=404)

        station = request.user.station
        sessions_qs = ChargingSession.objects.filter(station=station)

        summary = sessions_qs.aggregate(
            total_earnings=Sum('total_price'),
            total_watt=Sum('watt_consumed'),
            total_sessions=Count('id')
        )
        charger_usage = sessions_qs.values('charger__id', 'charger__name').annotate(
            sessions=Count('id'),
            earnings=Sum('total_price')
        )
        shift_history = ShiftRecord.objects.filter(station=station).values(
            'staff__id', 'staff__name', 'shift_start', 'shift_end',
            'kwh_start', 'kwh_end', 'kwh_consumed'
        ).order_by('-shift_start')

        return success_response(data={
            'summary': summary,
            'charger_usage': list(charger_usage),
            'shift_history': list(shift_history),
        })


class StationChargersView(APIView):
    """Staff views all chargers at their station."""
    permission_classes = [IsStaff]

    def get(self, request):
        if not request.user.station:
            return error_response(message="You are not assigned to any station")
        chargers = Charger.objects.filter(station=request.user.station)
        return success_response(data=ChargerSerializer(chargers, many=True).data)