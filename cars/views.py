from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view

from users.permissions import IsAdmin, IsAdminOrStaff
from users.exceptions import success_response, error_response
from .models import Car
from .serializers import (
    CarSerializer, CarRegisterSerializer,
    CarPaymentSerializer, CarPaymentInputSerializer,
)
from .services import CarPaymentService


@extend_schema_view(
    list=extend_schema(tags=['Cars'], summary='List cars (staff: no price, admin: with unique price)'),
    retrieve=extend_schema(tags=['Cars'], summary='Retrieve a car'),
    create=extend_schema(tags=['Cars'], summary='Create a car'),
    update=extend_schema(tags=['Cars'], summary='Update a car'),
    partial_update=extend_schema(tags=['Cars'], summary='Partially update a car'),
    destroy=extend_schema(tags=['Cars'], summary='Delete a car (admin only)'),
)
class CarViewSet(ModelViewSet):
    """Shared car management for staff and admin — only admin can read/set unique_price."""
    queryset = Car.objects.all()

    def get_permissions(self):
        if self.action in ('destroy', 'pay', 'balance'):
            return [IsAdmin()]
        return [IsAdminOrStaff()]

    def get_serializer_class(self):
        if getattr(self.request.user, 'role', None) == 'admin':
            return CarSerializer
        return CarRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            car = serializer.save()
            return success_response(data=serializer_class(car).data, message="Car created", status_code=201)
        return error_response(errors=serializer.errors)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            car = serializer.save()
            return success_response(data=serializer_class(car).data, message="Car updated")
        return error_response(errors=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Car deleted")

    def list(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        qs = self.get_queryset()
        return success_response(data=serializer_class(qs, many=True).data)

    @extend_schema(
        tags=['Cars'],
        summary='Record a payment against a car (admin only)',
        description=(
            'Records money paid by a postpaid car and settles its oldest unpaid '
            'charging sessions first (FIFO). Partial amounts are allowed; the '
            'amount may not exceed the outstanding balance.'
        ),
        request=CarPaymentInputSerializer,
        responses={201: CarPaymentSerializer},
    )
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        car = self.get_object()
        serializer = CarPaymentInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)
        try:
            payment, balance = CarPaymentService.record_payment(
                car=car,
                amount=serializer.validated_data['amount'],
                recorded_by=request.user,
                note=serializer.validated_data.get('note', ''),
            )
        except ValueError as e:
            return error_response(message=str(e))
        return success_response(
            data={'payment': CarPaymentSerializer(payment).data, 'balance': balance},
            message="Payment recorded",
            status_code=201,
        )

    @extend_schema(
        tags=['Cars'],
        summary="Get a car's charging balance and payment history (admin only)",
        responses={200: CarPaymentSerializer(many=True)},
    )
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        car = self.get_object()
        balance = CarPaymentService.get_balance(car)
        payments = CarPaymentSerializer(car.payments.all(), many=True).data
        return success_response(data={'balance': balance, 'payments': payments})
