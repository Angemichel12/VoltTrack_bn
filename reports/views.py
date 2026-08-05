from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from users.permissions import IsAdminOrStaff, IsAdmin
from users.exceptions import success_response, error_response
from .filters import filter_sessions, filter_shifts, filter_expenses, car_charge_summary
from .serializers import SessionReportSerializer, ShiftReportSerializer, ExpenseReportSerializer
from .columns import (
    SESSION_REPORT_COLUMNS, SHIFT_REPORT_COLUMNS, EXPENSE_REPORT_COLUMNS,
    CAR_SUMMARY_REPORT_COLUMNS,
)
from .exporters import build_excel_response, build_pdf_response


OWNER_FILTER_PARAM = OpenApiParameter(
    'owner', str,
    description='Filter by car owner name (exact). Use /api/cars/owners/?search= to look up owner names.',
)

COMMON_FILTER_PARAMS = [
    OpenApiParameter('staff', int, description='Admin only — filter by staff id. Staff are always scoped to their own data.'),
    OpenApiParameter('station', int, description='Filter by station id'),
    OWNER_FILTER_PARAM,
    OpenApiParameter('date_from', str, description='YYYY-MM-DD, inclusive'),
    OpenApiParameter('date_to', str, description='YYYY-MM-DD, inclusive'),
]

SESSION_FILTER_PARAMS = COMMON_FILTER_PARAMS + [
    OpenApiParameter('shift', int, description='Filter by shift id'),
    OpenApiParameter('charger', int, description='Filter by charger id'),
]

EXPENSE_FILTER_PARAMS = [
    OpenApiParameter('station', int, description='Filter by station id'),
    OpenApiParameter('date_from', str, description='YYYY-MM-DD, inclusive'),
    OpenApiParameter('date_to', str, description='YYYY-MM-DD, inclusive'),
]

CAR_SUMMARY_FILTER_PARAMS = [
    OpenApiParameter('station', int, description='Filter by station id'),
    OWNER_FILTER_PARAM,
    OpenApiParameter('date_from', str, description='YYYY-MM-DD, inclusive (on session start / payment date)'),
    OpenApiParameter('date_to', str, description='YYYY-MM-DD, inclusive'),
    OpenApiParameter('postpaid', bool, description='true = pay-later cars only, false = prepaid only'),
]


class SessionReportView(APIView):
    permission_classes = [IsAdminOrStaff]

    @extend_schema(
        tags=['Reports'],
        summary='Charging sessions report (filterable)',
        parameters=SESSION_FILTER_PARAMS,
        responses={200: SessionReportSerializer(many=True)},
    )
    def get(self, request):
        try:
            qs = filter_sessions(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(data=SessionReportSerializer(qs, many=True).data)


class SessionReportExcelView(APIView):
    permission_classes = [IsAdminOrStaff]

    @extend_schema(tags=['Reports'], summary='Download charging sessions report as Excel', parameters=SESSION_FILTER_PARAMS, responses={200: OpenApiTypes.BINARY})
    def get(self, request):
        try:
            qs = filter_sessions(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        rows = SessionReportSerializer(qs, many=True).data
        return build_excel_response('Charging Sessions', SESSION_REPORT_COLUMNS, rows, 'charging_sessions_report')


class SessionReportPdfView(APIView):
    permission_classes = [IsAdminOrStaff]

    @extend_schema(tags=['Reports'], summary='Download charging sessions report as PDF', parameters=SESSION_FILTER_PARAMS, responses={200: OpenApiTypes.BINARY})
    def get(self, request):
        try:
            qs = filter_sessions(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        rows = SessionReportSerializer(qs, many=True).data
        return build_pdf_response('Charging Sessions Report', SESSION_REPORT_COLUMNS, rows, 'charging_sessions_report')


class ShiftReportView(APIView):
    permission_classes = [IsAdminOrStaff]

    @extend_schema(
        tags=['Reports'],
        summary='Shift report (filterable)',
        parameters=COMMON_FILTER_PARAMS,
        responses={200: ShiftReportSerializer(many=True)},
    )
    def get(self, request):
        try:
            qs = filter_shifts(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(data=ShiftReportSerializer(qs, many=True).data)


class ShiftReportExcelView(APIView):
    permission_classes = [IsAdminOrStaff]

    @extend_schema(tags=['Reports'], summary='Download shift report as Excel', parameters=COMMON_FILTER_PARAMS, responses={200: OpenApiTypes.BINARY})
    def get(self, request):
        try:
            qs = filter_shifts(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        rows = ShiftReportSerializer(qs, many=True).data
        return build_excel_response('Shifts', SHIFT_REPORT_COLUMNS, rows, 'shift_report')


class ShiftReportPdfView(APIView):
    permission_classes = [IsAdminOrStaff]

    @extend_schema(tags=['Reports'], summary='Download shift report as PDF', parameters=COMMON_FILTER_PARAMS, responses={200: OpenApiTypes.BINARY})
    def get(self, request):
        try:
            qs = filter_shifts(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        rows = ShiftReportSerializer(qs, many=True).data
        return build_pdf_response('Shift Report', SHIFT_REPORT_COLUMNS, rows, 'shift_report')


class ExpenseReportView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags=['Reports'],
        summary='Station expenses report (filterable)',
        parameters=EXPENSE_FILTER_PARAMS,
        responses={200: ExpenseReportSerializer(many=True)},
    )
    def get(self, request):
        try:
            qs = filter_expenses(request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(data=ExpenseReportSerializer(qs, many=True).data)


class ExpenseReportExcelView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Reports'], summary='Download station expenses report as Excel', parameters=EXPENSE_FILTER_PARAMS, responses={200: OpenApiTypes.BINARY})
    def get(self, request):
        try:
            qs = filter_expenses(request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        rows = ExpenseReportSerializer(qs, many=True).data
        return build_excel_response('Expenses', EXPENSE_REPORT_COLUMNS, rows, 'expenses_report')


class ExpenseReportPdfView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Reports'], summary='Download station expenses report as PDF', parameters=EXPENSE_FILTER_PARAMS, responses={200: OpenApiTypes.BINARY})
    def get(self, request):
        try:
            qs = filter_expenses(request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        rows = ExpenseReportSerializer(qs, many=True).data
        return build_pdf_response('Expenses Report', EXPENSE_REPORT_COLUMNS, rows, 'expenses_report')


class CarSummaryReportView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags=['Reports'],
        summary='Per-car charging & payment summary (filterable)',
        description='Times charged, total amount, amount/times paid and outstanding balance per car.',
        parameters=CAR_SUMMARY_FILTER_PARAMS,
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        try:
            rows = car_charge_summary(request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(data=rows)


class CarSummaryReportExcelView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Reports'], summary='Download per-car summary report as Excel', parameters=CAR_SUMMARY_FILTER_PARAMS, responses={200: OpenApiTypes.BINARY})
    def get(self, request):
        try:
            rows = car_charge_summary(request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return build_excel_response('Car Summary', CAR_SUMMARY_REPORT_COLUMNS, rows, 'car_summary_report')


class CarSummaryReportPdfView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Reports'], summary='Download per-car summary report as PDF', parameters=CAR_SUMMARY_FILTER_PARAMS, responses={200: OpenApiTypes.BINARY})
    def get(self, request):
        try:
            rows = car_charge_summary(request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return build_pdf_response('Car Charging Summary Report', CAR_SUMMARY_REPORT_COLUMNS, rows, 'car_summary_report')
