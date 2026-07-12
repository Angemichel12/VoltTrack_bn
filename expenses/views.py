from django.utils.dateparse import parse_date
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from users.permissions import IsAdmin
from users.exceptions import success_response, error_response
from .models import Expense
from .serializers import ExpenseSerializer


def _filter_expenses(qs, params):
    station_id = params.get('station')
    if station_id:
        try:
            station_id = int(station_id)
        except (TypeError, ValueError):
            raise ValueError("'station' must be an integer.")
        qs = qs.filter(station_id=station_id)

    date_from = params.get('date_from')
    if date_from:
        parsed = parse_date(date_from)
        if parsed is None:
            raise ValueError("'date_from' must be a date in YYYY-MM-DD format.")
        qs = qs.filter(date__date__gte=parsed)

    date_to = params.get('date_to')
    if date_to:
        parsed = parse_date(date_to)
        if parsed is None:
            raise ValueError("'date_to' must be a date in YYYY-MM-DD format.")
        qs = qs.filter(date__date__lte=parsed)

    return qs


@extend_schema_view(
    list=extend_schema(
        tags=['Expenses'],
        summary='List expenses',
        parameters=[
            OpenApiParameter('station', int, description='Filter by station id'),
            OpenApiParameter('date_from', str, description='YYYY-MM-DD, inclusive'),
            OpenApiParameter('date_to', str, description='YYYY-MM-DD, inclusive'),
        ],
    ),
    retrieve=extend_schema(tags=['Expenses'], summary='Retrieve an expense'),
    create=extend_schema(tags=['Expenses'], summary='Create an expense'),
    update=extend_schema(tags=['Expenses'], summary='Update an expense'),
    partial_update=extend_schema(tags=['Expenses'], summary='Partially update an expense'),
    destroy=extend_schema(tags=['Expenses'], summary='Delete an expense'),
)
class ExpenseViewSet(ModelViewSet):
    """Admin-only station expense records. date is auto-set on creation."""
    permission_classes = [IsAdmin]
    serializer_class = ExpenseSerializer
    queryset = Expense.objects.select_related('station').all()

    def create(self, request, *args, **kwargs):
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            expense = serializer.save()
            return success_response(data=ExpenseSerializer(expense).data, message="Expense created", status_code=201)
        return error_response(errors=serializer.errors)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = ExpenseSerializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            expense = serializer.save()
            return success_response(data=ExpenseSerializer(expense).data, message="Expense updated")
        return error_response(errors=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Expense deleted")

    def list(self, request, *args, **kwargs):
        try:
            qs = _filter_expenses(self.get_queryset(), request.query_params)
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(data=ExpenseSerializer(qs, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=ExpenseSerializer(instance).data)
