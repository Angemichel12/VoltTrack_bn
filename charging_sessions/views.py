from rest_framework.views import APIView

from .models import ChargingSession
from .serializers import ChargingSessionSerializer, StartSessionSerializer, EndSessionSerializer
from .services import SessionService
from cars.models import Car
from cars.serializers import CarSerializer
from users.permissions import IsStaff
from users.exceptions import success_response, error_response


class RegisterCarView(APIView):
    permission_classes = [IsStaff]

    def post(self, request):
        serializer = CarSerializer(data=request.data)
        if serializer.is_valid():
            plate = serializer.validated_data['plate_number'].upper().strip()
            car, created = Car.objects.get_or_create(
                plate_number=plate,
                defaults={'optional_info': serializer.validated_data.get('optional_info', '')}
            )
            return success_response(
                data=CarSerializer(car).data,
                message="Car registered" if created else "Car already exists",
                status_code=201 if created else 200
            )
        return error_response(errors=serializer.errors)


class SearchCarView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        plate = request.query_params.get('plate')
        if not plate:
            return error_response(message="plate query parameter is required")
        try:
            car = Car.objects.get(plate_number=plate.upper().strip())
            return success_response(data=CarSerializer(car).data)
        except Car.DoesNotExist:
            return error_response(message="Car not found", status_code=404)


class StartSessionView(APIView):
    permission_classes = [IsStaff]

    def post(self, request):
        if not request.user.station:
            return error_response(message="You are not assigned to any station")

        serializer = StartSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        try:
            session = SessionService.start_session(
                staff=request.user,
                charger_id=serializer.validated_data['charger_id'],
                plate_number=serializer.validated_data['plate_number']
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

    def post(self, request):
        serializer = EndSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        try:
            session = SessionService.end_session(
                staff=request.user,
                session_id=serializer.validated_data['session_id'],
                watt_consumed=serializer.validated_data['watt_consumed']
            )
            return success_response(
                data=ChargingSessionSerializer(session).data,
                message="Session ended successfully"
            )
        except ValueError as e:
            return error_response(message=str(e))


class MySessionsView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        sessions = ChargingSession.objects.filter(
            staff=request.user
        ).select_related('car', 'charger', 'station').order_by('-started_at')
        return success_response(data=ChargingSessionSerializer(sessions, many=True).data)