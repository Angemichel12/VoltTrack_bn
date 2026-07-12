from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from users.permissions import IsAdminOrStaff
from users.exceptions import success_response, error_response
from .services import DashboardService


FILTER_PARAMS = [
    OpenApiParameter('station', int, description='Filter by station id. Staff are always scoped to stations they worked.'),
    OpenApiParameter('date_from', str, description='YYYY-MM-DD, inclusive'),
    OpenApiParameter('date_to', str, description='YYYY-MM-DD, inclusive'),
]


class DashboardSummaryView(APIView):
    """KPI tiles: revenue, sessions, kWh used, shifts, stations touched — plus expenses/net revenue for admin."""
    permission_classes = [IsAdminOrStaff]

    @extend_schema(tags=['Dashboard'], summary='Dashboard KPI tiles', parameters=FILTER_PARAMS, responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        try:
            data = DashboardService.summary(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(data=data)


class RevenueTrendView(APIView):
    """Line-chart data: revenue by day (admin responses also include expenses per day)."""
    permission_classes = [IsAdminOrStaff]

    @extend_schema(tags=['Dashboard'], summary='Revenue (and, for admin, expenses) grouped by day', parameters=FILTER_PARAMS, responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        try:
            data = DashboardService.revenue_trend(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(data=data)


class StationUsageView(APIView):
    """Bar-chart data: sessions, kWh used and revenue per station."""
    permission_classes = [IsAdminOrStaff]

    @extend_schema(tags=['Dashboard'], summary='Sessions, kWh used and revenue grouped by station', parameters=FILTER_PARAMS, responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        try:
            data = DashboardService.station_usage(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(data=data)


class ShiftActivityView(APIView):
    """Line/bar-chart data: shift counts and totals per day."""
    permission_classes = [IsAdminOrStaff]

    @extend_schema(tags=['Dashboard'], summary='Shift counts and totals grouped by day', parameters=FILTER_PARAMS, responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        try:
            data = DashboardService.shift_activity(request.user, request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(data=data)
