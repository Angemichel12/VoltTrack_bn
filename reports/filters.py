from django.utils.dateparse import parse_date
from django.db.models import Count, Sum
from charging_sessions.models import ChargingSession
from chargers.models import ShiftRecord
from expenses.models import Expense
from cars.models import CarPayment


def _parse_int(params, key):
    value = params.get(key)
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' must be an integer.")


def _parse_date(params, key):
    value = params.get(key)
    if value in (None, ''):
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise ValueError(f"'{key}' must be a date in YYYY-MM-DD format.")
    return parsed


def _parse_bool(params, key):
    value = params.get(key)
    if value in (None, ''):
        return None
    return str(value).strip().lower() in ('true', '1', 'yes')


def _parse_str(params, key):
    value = params.get(key)
    if value in (None, ''):
        return None
    return str(value).strip()


def filter_sessions(user, params):
    """Charging sessions report queryset. Staff are always scoped to their own sessions."""
    qs = ChargingSession.objects.select_related('station', 'charger', 'staff', 'car', 'shift')

    if user.role == 'staff':
        qs = qs.filter(staff=user)
    else:
        staff_id = _parse_int(params, 'staff')
        if staff_id is not None:
            qs = qs.filter(staff_id=staff_id)

    shift_id = _parse_int(params, 'shift')
    if shift_id is not None:
        qs = qs.filter(shift_id=shift_id)

    station_id = _parse_int(params, 'station')
    if station_id is not None:
        qs = qs.filter(station_id=station_id)

    charger_id = _parse_int(params, 'charger')
    if charger_id is not None:
        qs = qs.filter(charger_id=charger_id)

    owner = _parse_str(params, 'owner')
    if owner is not None:
        qs = qs.filter(car__owner_name=owner)

    date_from = _parse_date(params, 'date_from')
    if date_from is not None:
        qs = qs.filter(started_at__date__gte=date_from)

    date_to = _parse_date(params, 'date_to')
    if date_to is not None:
        qs = qs.filter(started_at__date__lte=date_to)

    return qs.order_by('-started_at')


def filter_shifts(user, params):
    """Shift report queryset. Staff are always scoped to their own shifts."""
    qs = ShiftRecord.objects.select_related('station', 'staff')

    if user.role == 'staff':
        qs = qs.filter(staff=user)
    else:
        staff_id = _parse_int(params, 'staff')
        if staff_id is not None:
            qs = qs.filter(staff_id=staff_id)

    station_id = _parse_int(params, 'station')
    if station_id is not None:
        qs = qs.filter(station_id=station_id)

    # A shift isn't tied to a car directly; filter to shifts that include at
    # least one charging session for one of the selected owner's cars.
    owner = _parse_str(params, 'owner')
    if owner is not None:
        qs = qs.filter(sessions__car__owner_name=owner).distinct()

    date_from = _parse_date(params, 'date_from')
    if date_from is not None:
        qs = qs.filter(shift_start__date__gte=date_from)

    date_to = _parse_date(params, 'date_to')
    if date_to is not None:
        qs = qs.filter(shift_start__date__lte=date_to)

    return qs.order_by('-shift_start')


def filter_expenses(params):
    """Expenses report queryset. Admin-only resource — no per-staff scoping."""
    qs = Expense.objects.select_related('station')

    station_id = _parse_int(params, 'station')
    if station_id is not None:
        qs = qs.filter(station_id=station_id)

    date_from = _parse_date(params, 'date_from')
    if date_from is not None:
        qs = qs.filter(date__date__gte=date_from)

    date_to = _parse_date(params, 'date_to')
    if date_to is not None:
        qs = qs.filter(date__date__lte=date_to)

    return qs.order_by('-date')


def car_charge_summary(params):
    """Per-car charging + payment summary. Admin-only resource — no per-staff scoping.

    Returns a list of dicts (one per car that has priced sessions), each with
    charge counts/totals, amount paid, number of payments, and the outstanding
    balance. Filterable by station, date range (on session start), and a
    `postpaid` flag.
    """
    sessions = ChargingSession.objects.filter(total_price__isnull=False)

    station_id = _parse_int(params, 'station')
    if station_id is not None:
        sessions = sessions.filter(station_id=station_id)

    date_from = _parse_date(params, 'date_from')
    if date_from is not None:
        sessions = sessions.filter(started_at__date__gte=date_from)

    date_to = _parse_date(params, 'date_to')
    if date_to is not None:
        sessions = sessions.filter(started_at__date__lte=date_to)

    postpaid = _parse_bool(params, 'postpaid')
    if postpaid is not None:
        sessions = sessions.filter(car__is_postpaid=postpaid)

    owner = _parse_str(params, 'owner')
    if owner is not None:
        sessions = sessions.filter(car__owner_name=owner)

    rows = (
        sessions
        .values('car_id', 'car__plate_number', 'car__owner_name', 'car__is_postpaid')
        .annotate(
            times_charged=Count('id'),
            total_amount=Sum('total_price'),
            amount_paid=Sum('amount_paid'),
        )
    )

    # Payment counts per car, honoring the same date/station scope isn't
    # meaningful for payments (they aren't tied to a station), so we count all
    # payments per car within the date range on paid_at.
    payments = CarPayment.objects.all()
    if date_from is not None:
        payments = payments.filter(paid_at__date__gte=date_from)
    if date_to is not None:
        payments = payments.filter(paid_at__date__lte=date_to)
    times_paid_by_car = {
        row['car_id']: row['times_paid']
        for row in payments.values('car_id').annotate(times_paid=Count('id'))
    }

    summary = []
    for row in rows:
        total_amount = row['total_amount'] or 0
        amount_paid = row['amount_paid'] or 0
        summary.append({
            'car_id': row['car_id'],
            'plate_number': row['car__plate_number'],
            'owner_name': row['car__owner_name'],
            'is_postpaid': row['car__is_postpaid'],
            'times_charged': row['times_charged'],
            'total_amount': total_amount,
            'amount_paid': amount_paid,
            'times_paid': times_paid_by_car.get(row['car_id'], 0),
            'outstanding': total_amount - amount_paid,
        })

    summary.sort(key=lambda r: r['outstanding'], reverse=True)
    return summary
