from django.utils.dateparse import parse_date
from charging_sessions.models import ChargingSession
from chargers.models import ShiftRecord
from expenses.models import Expense


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
