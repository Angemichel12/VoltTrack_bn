from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view

from users.permissions import IsAdmin, IsAdminOrStaff
from users.exceptions import success_response, error_response
from .models import Car
from .serializers import CarSerializer, CarRegisterSerializer


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
        if self.action == 'destroy':
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
