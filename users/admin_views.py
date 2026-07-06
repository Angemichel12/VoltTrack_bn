from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from users.models import User
from users.serializers import AdminCreateUserSerializer, UserSerializer
from stations.models import Station
from stations.serializers import StationSerializer
from .permissions import IsAdmin
from .exceptions import success_response, error_response


@extend_schema_view(
    list=extend_schema(
        tags=['Admin · Users'],
        summary='List users',
        parameters=[OpenApiParameter('role', str, description='Filter by role (admin/manager/staff)')],
    ),
    retrieve=extend_schema(tags=['Admin · Users'], summary='Retrieve a user'),
    create=extend_schema(tags=['Admin · Users'], summary='Create a user', request=AdminCreateUserSerializer, responses={201: UserSerializer}),
    update=extend_schema(tags=['Admin · Users'], summary='Update a user'),
    partial_update=extend_schema(tags=['Admin · Users'], summary='Partially update a user'),
    destroy=extend_schema(tags=['Admin · Users'], summary='Delete a user'),
)
class AdminUserViewSet(ModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminCreateUserSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = AdminCreateUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return success_response(
                data=UserSerializer(user).data,
                message="User created successfully",
                status_code=201
            )
        return error_response(errors=serializer.errors)

    def list(self, request, *args, **kwargs):
        role = request.query_params.get('role')
        qs = self.get_queryset()
        if role:
            qs = qs.filter(role=role)
        return success_response(data=UserSerializer(qs, many=True).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="User deleted successfully")


@extend_schema_view(
    list=extend_schema(tags=['Admin · Stations'], summary='List stations'),
    retrieve=extend_schema(tags=['Admin · Stations'], summary='Retrieve a station'),
    create=extend_schema(tags=['Admin · Stations'], summary='Create a station'),
    update=extend_schema(tags=['Admin · Stations'], summary='Update a station'),
    partial_update=extend_schema(tags=['Admin · Stations'], summary='Partially update a station'),
    destroy=extend_schema(tags=['Admin · Stations'], summary='Delete a station'),
)
class AdminStationViewSet(ModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = StationSerializer
    queryset = Station.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = StationSerializer(data=request.data)
        if serializer.is_valid():
            station = serializer.save()
            return success_response(data=StationSerializer(station).data, message="Station created", status_code=201)
        return error_response(errors=serializer.errors)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = StationSerializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            station = serializer.save()
            return success_response(data=StationSerializer(station).data, message="Station updated")
        return error_response(errors=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Station deleted")

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return success_response(data=StationSerializer(qs, many=True).data)

    @extend_schema(tags=['Admin · Stations'], summary='System-wide charging reports')
    @action(detail=False, methods=['get'], url_path='reports')
    def system_reports(self, request):
        from charging_sessions.models import ChargingSession
        from django.db.models import Sum, Count
        stats = ChargingSession.objects.aggregate(
            total_earnings=Sum('total_price'),
            total_watt=Sum('watt_consumed'),
            total_sessions=Count('id')
        )
        per_station = ChargingSession.objects.values(
            'station__id', 'station__name'
        ).annotate(
            earnings=Sum('total_price'),
            watt_used=Sum('watt_consumed'),
            sessions=Count('id')
        )
        return success_response(data={
            'system_summary': stats,
            'per_station': list(per_station)
        })