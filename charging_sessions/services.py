from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone
from django.db.models import F
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
    def estimate_watt_consumed(car, starting_pct, ending_pct):
        """Estimate kWh used from the car's most recent completed charge.

        Takes the car's last *real* (non-estimated) completed session, derives its
        per-percent rate = watt_consumed / (ending% - starting%), and multiplies by
        this session's (ending% - starting%). Returns a Decimal, or None if the car
        has no usable history to estimate from.
        """
        if starting_pct is None or ending_pct is None:
            raise ValueError("Both starting and ending percentages are required to estimate usage.")

        delta = ending_pct - starting_pct
        if delta <= 0:
            raise ValueError("Ending percentage must be greater than starting percentage.")

        last = (
            ChargingSession.objects.filter(
                car=car,
                ended_at__isnull=False,
                is_estimated=False,
                watt_consumed__isnull=False,
                starting_car_percentage__isnull=False,
                ending_car_percentage__isnull=False,
                ending_car_percentage__gt=F('starting_car_percentage'),
            )
            .order_by('-ended_at')
            .first()
        )
        if last is None:
            return None

        rate = last.watt_consumed / Decimal(last.ending_car_percentage - last.starting_car_percentage)
        estimated = rate * Decimal(delta)
        return estimated.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def end_session(staff, session_id, ending_car_percentage, watt_consumed=None, power_outage=False):
        try:
            session = ChargingSession.objects.select_related('station', 'car').get(
                id=session_id,
                staff=staff,
                ended_at__isnull=True
            )
        except ChargingSession.DoesNotExist:
            raise ValueError("Active session not found or does not belong to you.")

        if power_outage and watt_consumed is None:
            estimated = SessionService.estimate_watt_consumed(
                session.car, session.starting_car_percentage, ending_car_percentage
            )
            if estimated is None:
                raise ValueError(
                    "No charging history for this car yet, so kWh can't be estimated. "
                    "Please enter the kWh used manually."
                )
            session.watt_consumed = estimated
            session.is_estimated = True
        else:
            if watt_consumed is None:
                raise ValueError("watt_consumed is required to end a session.")
            session.watt_consumed = watt_consumed
            session.is_estimated = False

        session.ending_car_percentage = ending_car_percentage
        session.ended_at = timezone.now()
        session.save()
        return session
