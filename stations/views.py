from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from drf_spectacular.utils import extend_schema, OpenApiTypes

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
    """List is available to any authenticated user (staff need it to pick a station when opening a shift). Create is admin-only."""

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [IsAuthenticated()]

    @extend_schema(tags=['Stations'], summary='List all stations', responses={200: StationSerializer(many=True)})
    def get(self, request):
        stations = Station.objects.all()
        return success_response(data=StationSerializer(stations, many=True).data)

    @extend_schema(tags=['Stations'], summary='Create a station', request=StationSerializer, responses={201: StationSerializer})
    def post(self, request):
        serializer = StationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Station created", status_code=201)


class AdminStationDetailView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Stations'], summary='Update a station', request=StationSerializer, responses={200: StationSerializer})
    def patch(self, request, pk):
        from django.shortcuts import get_object_or_404
        station = get_object_or_404(Station, pk=pk)
        serializer = StationSerializer(station, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Station updated")

    @extend_schema(tags=['Stations'], summary='Delete a station', responses={200: OpenApiTypes.OBJECT})
    def delete(self, request, pk):
        from django.shortcuts import get_object_or_404
        station = get_object_or_404(Station, pk=pk)
        station.delete()
        return success_response(message="Station deleted")


class AdminReportsView(APIView):
    """Admin-level report across all stations."""
    permission_classes = [IsAdmin]

    @extend_schema(
        tags=['Reports'],
        summary='System-wide earnings/usage report across all stations',
        responses={200: OpenApiTypes.OBJECT},
    )
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

    @extend_schema(
        tags=['Stations'],
        summary='Staff dashboard summary for their current open shift',
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        open_shift = ShiftRecord.get_open_for(request.user)
        if not open_shift:
            return error_response(message="You have no open shift. Open a shift to see your dashboard.", status_code=404)

        station = open_shift.station
        charger_count = Charger.objects.filter(station=station).count()
        session_stats = ChargingSession.objects.filter(shift=open_shift).aggregate(
            total_sessions=Count('id'),
            total_earnings=Sum('total_price'),
            total_watt=Sum('watt_consumed')
        )

        return success_response(data={
            'station': StationSerializer(station).data,
            'charger_count': charger_count,
            'open_shift': ShiftRecordSerializer(open_shift).data,
            **session_stats
        })


class SetPriceView(APIView):
    """Admin sets price per watt for a station."""
    permission_classes = [IsAdmin]

    @extend_schema(
        tags=['Stations'],
        summary='Set price per watt for a station',
        request=OpenApiTypes.OBJECT,
        responses={200: StationSerializer},
    )
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
    """Staff sees their own personal reports, across every station they've worked at."""
    permission_classes = [IsStaff]

    @extend_schema(
        tags=['Reports'],
        summary='Personal report for the staff member, across all stations worked',
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        sessions_qs = ChargingSession.objects.filter(staff=request.user)

        summary = sessions_qs.aggregate(
            total_earnings=Sum('total_price'),
            total_watt=Sum('watt_consumed'),
            total_sessions=Count('id')
        )
        charger_usage = sessions_qs.values('charger__id', 'charger__name').annotate(
            sessions=Count('id'),
            earnings=Sum('total_price')
        )
        shift_history = ShiftRecord.objects.filter(staff=request.user).values(
            'id', 'station__id', 'station__name', 'shift_start', 'shift_end',
            'start_kwatts_in_cashpower', 'addition_kwatt_in_cashpower', 'total_kwatt',
            'total_earned_money_on_shift', 'total_kwatt_used_on_shift',
            'total_car_charged', 'money_on_momo', 'end_kwatts_in_cashpower',
        ).order_by('-shift_start')

        return success_response(data={
            'summary': summary,
            'charger_usage': list(charger_usage),
            'shift_history': list(shift_history),
        })


class StationChargersView(APIView):
    """Staff views all chargers at their station."""
    permission_classes = [IsStaff]

    @extend_schema(
        tags=['Stations'],
        summary='List chargers at the staff member\'s current open-shift station',
        responses={200: ChargerSerializer(many=True)},
    )
    def get(self, request):
        open_shift = ShiftRecord.get_open_for(request.user)
        if not open_shift:
            return error_response(message="You must open a shift before viewing chargers.")
        chargers = Charger.objects.filter(station=open_shift.station)
        return success_response(data=ChargerSerializer(chargers, many=True).data)