from django.utils import timezone
from charging_sessions.models import ChargingSession
from chargers.models import Charger
from cars.models import Car


class SessionService:

    @staticmethod
    def start_session(staff, charger_id, plate_number):
        try:
            charger = Charger.objects.select_related('station').get(
                id=charger_id,
                station=staff.station   # staff can use any charger at their station
            )
        except Charger.DoesNotExist:
            raise ValueError("Charger not found at your station.")

        station = charger.station

        if not station.price_per_watt:
            raise ValueError("Price per watt has not been set for this station.")

        # Ensure staff has an open shift before starting a session
        from chargers.models import ShiftRecord
        if not ShiftRecord.objects.filter(
            station=station, staff=staff, shift_end__isnull=True
        ).exists():
            raise ValueError("You must open a shift before starting a session.")

        car, _ = Car.objects.get_or_create(plate_number=plate_number.upper().strip())

        if ChargingSession.objects.filter(charger=charger, ended_at__isnull=True).exists():
            raise ValueError("This charger already has an active session.")

        return ChargingSession.objects.create(
            station=station,
            charger=charger,
            staff=staff,
            car=car,
        )

    @staticmethod
    def end_session(staff, session_id, watt_consumed):
        try:
            session = ChargingSession.objects.select_related('station').get(
                id=session_id,
                staff=staff,
                ended_at__isnull=True
            )
        except ChargingSession.DoesNotExist:
            raise ValueError("Active session not found or does not belong to you.")

        session.watt_consumed = watt_consumed
        session.ended_at = timezone.now()
        session.save()
        return session