from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import ChargingSession
from .serializers import ChargingSessionSerializer, StartSessionSerializer, EndSessionSerializer
from .services import SessionService
from cars.models import Car
from cars.serializers import CarSerializer, CarRegisterSerializer
from users.permissions import IsStaff, IsAdminOrStaff
from users.exceptions import success_response, error_response


class RegisterCarView(APIView):
    permission_classes = [IsAdminOrStaff]

    @extend_schema(
        tags=['Cars'],
        summary='Register a car (or return the existing one for that plate)',
        request=CarRegisterSerializer,
        responses={200: CarRegisterSerializer, 201: CarRegisterSerializer},
    )
    def post(self, request):
        serializer = CarRegisterSerializer(data=request.data)
        if serializer.is_valid():
            plate = serializer.validated_data['plate_number'].upper().strip()
            car, created = Car.objects.get_or_create(
                plate_number=plate,
                defaults={
                    'owner_name': serializer.validated_data.get('owner_name', ''),
                    'phone_number': serializer.validated_data.get('phone_number', ''),
                    'optional_info': serializer.validated_data.get('optional_info', ''),
                }
            )
            return success_response(
                data=CarRegisterSerializer(car).data,
                message="Car registered" if created else "Car already exists",
                status_code=201 if created else 200
            )
        return error_response(errors=serializer.errors)


class SearchCarView(APIView):
    """Incremental plate search — matches on any characters typed so far, for a type-ahead pick list."""
    permission_classes = [IsAdminOrStaff]
    MAX_RESULTS = 20

    @extend_schema(
        tags=['Cars'],
        summary='Search cars by partial plate number (type-ahead)',
        parameters=[OpenApiParameter('plate', str, required=True, description='Characters typed so far — matches anywhere in the plate number')],
        responses={200: CarRegisterSerializer(many=True)},
    )
    def get(self, request):
        plate = request.query_params.get('plate')
        if not plate:
            return error_response(message="plate query parameter is required")

        serializer_class = CarSerializer if request.user.role == 'admin' else CarRegisterSerializer
        cars = Car.objects.filter(
            plate_number__icontains=plate.upper().strip()
        ).order_by('plate_number')[:self.MAX_RESULTS]
        return success_response(data=serializer_class(cars, many=True).data)


class StartSessionView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(
        tags=['Charging Sessions'],
        summary='Start a charging session at your station',
        request=StartSessionSerializer,
        responses={201: ChargingSessionSerializer},
    )
    def post(self, request):
        serializer = StartSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        try:
            session = SessionService.start_session(
                staff=request.user,
                charger_id=serializer.validated_data['charger_id'],
                port=serializer.validated_data['port'],
                plate_number=serializer.validated_data['plate_number'],
                starting_car_percentage=serializer.validated_data['starting_car_percentage'],
            )
            return success_response(
                data=ChargingSessionSerializer(session).data,
                message="Session started",
                status_code=201
            )
        except ValueError as e:
            return error_response(message=str(e))


class EndSessionView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(
        tags=['Charging Sessions'],
        summary='End a charging session',
        description=(
            'Normally staff supply the metered kWh in `watt_consumed`. When the '
            'grid power went off mid-charge and the meter can\'t be read, send '
            '`power_outage=true` and omit `watt_consumed`: the kWh used is then '
            'estimated from the car\'s past charging history (average kWh per '
            'battery %, applied to this session\'s start/end %), and the result '
            'is flagged with `is_estimated=true`. If the car has no history yet, '
            'the request is rejected and staff must enter `watt_consumed` manually.'
        ),
        request=EndSessionSerializer,
        responses={200: ChargingSessionSerializer},
    )
    def post(self, request):
        serializer = EndSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        try:
            session = SessionService.end_session(
                staff=request.user,
                session_id=serializer.validated_data['session_id'],
                ending_car_percentage=serializer.validated_data['ending_car_percentage'],
                watt_consumed=serializer.validated_data.get('watt_consumed'),
                power_outage=serializer.validated_data.get('power_outage', False),
            )
            return success_response(
                data=ChargingSessionSerializer(session).data,
                message="Session ended successfully"
            )
        except ValueError as e:
            return error_response(message=str(e))


class MySessionsView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(
        tags=['Charging Sessions'],
        summary='List your own charging sessions',
        responses={200: ChargingSessionSerializer(many=True)},
    )
    def get(self, request):
        sessions = ChargingSession.objects.filter(
            staff=request.user
        ).select_related('car', 'charger', 'station').order_by('-started_at')
        return success_response(data=ChargingSessionSerializer(sessions, many=True).data)