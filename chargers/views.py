from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiTypes

from .models import Charger, ShiftRecord
from .serializers import (
    ChargerSerializer, ShiftRecordSerializer,
    OpenShiftSerializer, CloseShiftSerializer, AddCashpowerSerializer
)
from users.permissions import IsAdmin, IsStaff
from users.exceptions import success_response, error_response


class ChargerListCreateView(APIView):
    """Admin: full CRUD. Staff: read chargers at their station only."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Chargers'],
        summary='List chargers (admin: all, staff: own station)',
        responses={200: ChargerSerializer(many=True)},
    )
    def get(self, request):
        if request.user.role == 'admin':
            chargers = Charger.objects.select_related('station').all()
        else:
            open_shift = ShiftRecord.get_open_for(request.user)
            if not open_shift:
                return error_response(message="You must open a shift before viewing chargers.")
            chargers = Charger.objects.select_related('station').filter(
                station=open_shift.station
            )
        return success_response(data=ChargerSerializer(chargers, many=True).data)

    @extend_schema(
        tags=['Chargers'],
        summary='Create a charger (admin only)',
        request=ChargerSerializer,
        responses={201: ChargerSerializer},
    )
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

    @extend_schema(tags=['Chargers'], summary='Delete a charger (admin only)', responses={200: OpenApiTypes.OBJECT})
    def delete(self, request, pk):
        if request.user.role != 'admin':
            return error_response(message="Admin only.", status_code=403)
        charger = get_object_or_404(Charger, pk=pk)
        charger.delete()
        return success_response(message="Charger deleted")


class OpenShiftView(APIView):
    """Staff selects a station and opens a shift there — records starting CashPower balance."""
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        tags=['Shifts'],
        summary='Open a shift at a station of your choice',
        request=OpenShiftSerializer,
        responses={201: ShiftRecordSerializer},
    )
    def post(self, request):
        # A staff member can only work one shift at a time, regardless of station
        if ShiftRecord.get_open_for(request.user):
            return error_response(message="You already have an open shift. End it before opening a new one.")

        serializer = OpenShiftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = serializer.save(staff=request.user)
        return success_response(
            data=ShiftRecordSerializer(record).data,
            message="Shift opened",
            status_code=201
        )


class AddCashpowerView(APIView):
    """Staff tops up the CashPower balance on their open shift."""
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        tags=['Shifts'],
        summary='Add CashPower kWh to your open shift',
        request=AddCashpowerSerializer,
        responses={200: ShiftRecordSerializer},
    )
    def patch(self, request, pk):
        record = get_object_or_404(
            ShiftRecord, pk=pk, staff=request.user, shift_end__isnull=True
        )
        serializer = AddCashpowerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record.add_cashpower(serializer.validated_data['amount'])
        return success_response(
            data=ShiftRecordSerializer(record).data,
            message="CashPower added"
        )


class CloseShiftView(APIView):
    """Staff closes their open shift — records ending kWh and computes consumed."""
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        tags=['Shifts'],
        summary='Close your open shift',
        request=CloseShiftSerializer,
        responses={200: ShiftRecordSerializer},
    )
    def patch(self, request, pk):
        record = get_object_or_404(
            ShiftRecord, pk=pk, staff=request.user, shift_end__isnull=True
        )
        serializer = CloseShiftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        record.notes = serializer.validated_data.get('notes', record.notes)
        record.close_shift(
            money_on_momo=serializer.validated_data['money_on_momo'],
            end_kwatts_in_cashpower=serializer.validated_data['end_kwatts_in_cashpower'],
        )

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

    @extend_schema(
        tags=['Shifts'],
        summary='List shift history (admin: all, staff: own)',
        responses={200: ShiftRecordSerializer(many=True)},
    )
    def get(self, request):
        if request.user.role == 'admin':
            records = ShiftRecord.objects.select_related('station', 'staff').all()
        else:
            records = ShiftRecord.objects.select_related('station', 'staff').filter(
                staff=request.user
            )
        return success_response(data=ShiftRecordSerializer(records, many=True).data)