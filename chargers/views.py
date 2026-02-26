from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Charger, ShiftRecord
from .serializers import (
    ChargerSerializer, ShiftRecordSerializer,
    OpenShiftSerializer, CloseShiftSerializer
)
from users.permissions import IsAdmin, IsStaff
from users.exceptions import success_response, error_response


class ChargerListCreateView(APIView):
    """Admin: full CRUD. Staff: read chargers at their station only."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'admin':
            chargers = Charger.objects.select_related('station').all()
        else:
            if not request.user.station:
                return error_response(message="You are not assigned to any station")
            chargers = Charger.objects.select_related('station').filter(
                station=request.user.station
            )
        return success_response(data=ChargerSerializer(chargers, many=True).data)

    def post(self, request):
        if request.user.role != 'admin':
            return error_response(message="Admin only.", status_code=403)
        serializer = ChargerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data,
            message="Charger created",
            status_code=201
        )

    def delete(self, request, pk):
        if request.user.role != 'admin':
            return error_response(message="Admin only.", status_code=403)
        charger = get_object_or_404(Charger, pk=pk)
        charger.delete()
        return success_response(message="Charger deleted")


class OpenShiftView(APIView):
    """Staff opens a shift at their station — records starting kWh."""
    permission_classes = [IsAuthenticated, IsStaff]

    def post(self, request):
        if not request.user.station:
            return error_response(message="You are not assigned to any station")

        station_id = request.user.station.id

        # Block duplicate open shifts at the same station
        if ShiftRecord.objects.filter(
            station_id=station_id,
            staff=request.user,
            shift_end__isnull=True
        ).exists():
            return error_response(message="You already have an open shift at this station.")

        serializer = OpenShiftSerializer(data={**request.data, 'station': station_id})
        serializer.is_valid(raise_exception=True)
        record = serializer.save(staff=request.user)
        return success_response(
            data=ShiftRecordSerializer(record).data,
            message="Shift opened",
            status_code=201
        )


class CloseShiftView(APIView):
    """Staff closes their open shift — records ending kWh and computes consumed."""
    permission_classes = [IsAuthenticated, IsStaff]

    def patch(self, request, pk):
        record = get_object_or_404(
            ShiftRecord, pk=pk, staff=request.user, shift_end__isnull=True
        )
        serializer = CloseShiftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data['kwh_end'] <= record.kwh_start:
            return error_response(message="kwh_end must be greater than kwh_start.")

        record.notes = serializer.validated_data.get('notes', record.notes)
        record.close_shift(kwh_end=serializer.validated_data['kwh_end'])

        return success_response(
            data=ShiftRecordSerializer(record).data,
            message="Shift closed successfully"
        )


class ShiftHistoryView(APIView):
    """
    Admin: all shift records across all stations.
    Staff: only their own records.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'admin':
            records = ShiftRecord.objects.select_related('station', 'staff').all()
        else:
            records = ShiftRecord.objects.select_related('station', 'staff').filter(
                staff=request.user
            )
        return success_response(data=ShiftRecordSerializer(records, many=True).data)