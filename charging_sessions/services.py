from django.utils import timezone
from charging_sessions.models import ChargingSession
from chargers.models import Charger, ShiftRecord
from cars.models import Car


class SessionService:

    @staticmethod
    def start_session(staff, charger_id, port, plate_number, starting_car_percentage):
        open_shift = ShiftRecord.get_open_for(staff)
        if not open_shift:
            raise ValueError("You must open a shift before starting a session.")

        try:
            charger = Charger.objects.select_related('station').get(
                id=charger_id,
                station=open_shift.station   # staff can use any charger at their shift's station
            )
        except Charger.DoesNotExist:
            raise ValueError("Charger not found at your shift's station.")

        station = charger.station

        if not station.price_per_watt:
            raise ValueError("Price per watt has not been set for this station.")

        car, _ = Car.objects.get_or_create(plate_number=plate_number.upper().strip())

        if ChargingSession.objects.filter(charger=charger, port=port, ended_at__isnull=True).exists():
            raise ValueError(f"Port {port} on this charger is already in use.")

        return ChargingSession.objects.create(
            station=station,
            charger=charger,
            port=port,
            staff=staff,
            shift=open_shift,
            car=car,
            starting_car_percentage=starting_car_percentage,
        )

    @staticmethod
    def end_session(staff, session_id, watt_consumed, ending_car_percentage):
        try:
            session = ChargingSession.objects.select_related('station', 'car').get(
                id=session_id,
                staff=staff,
                ended_at__isnull=True
            )
        except ChargingSession.DoesNotExist:
            raise ValueError("Active session not found or does not belong to you.")

        session.watt_consumed = watt_consumed
        session.ending_car_percentage = ending_car_percentage
        session.ended_at = timezone.now()
        session.save()
        return session