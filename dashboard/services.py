from django.db.models import Sum, Count
from django.db.models.functions import TruncDate

from reports.filters import filter_sessions, filter_shifts, filter_expenses


class DashboardService:
    """Aggregations for the dashboard graphs. Scoping (staff vs admin) is
    inherited from reports.filters — staff always see only their own sessions
    and shifts; expenses are admin-only, so they're skipped for staff."""

    @staticmethod
    def summary(user, params):
        sessions_qs = filter_sessions(user, params)
        shifts_qs = filter_shifts(user, params)

        totals = sessions_qs.aggregate(
            total_revenue=Sum('total_price'),
            total_kwatt_used=Sum('watt_consumed'),
            total_sessions=Count('id'),
        )

        data = {
            'total_revenue': totals['total_revenue'] or 0,
            'total_kwatt_used': totals['total_kwatt_used'] or 0,
            'total_sessions': totals['total_sessions'] or 0,
            'total_shifts': shifts_qs.count(),
            'stations': sessions_qs.values('station_id').distinct().count(),
        }

        if user.role != 'staff':
            expense_totals = filter_expenses(params).aggregate(
                vat_exclusive=Sum('amount_vat_exclusive'),
                input_vat=Sum('input_vat'),
            )
            total_expenses = (expense_totals['vat_exclusive'] or 0) + (expense_totals['input_vat'] or 0)
            data['total_expenses'] = total_expenses
            data['net_revenue'] = data['total_revenue'] - total_expenses

        return data

    @staticmethod
    def revenue_trend(user, params):
        """Revenue by day; admin responses also carry an 'expenses' figure per day."""
        sessions_qs = filter_sessions(user, params)
        revenue_by_day = (
            sessions_qs
            .annotate(day=TruncDate('started_at'))
            .values('day')
            .annotate(revenue=Sum('total_price'))
        )
        trend = {
            row['day']: {'date': row['day'], 'revenue': row['revenue'] or 0}
            for row in revenue_by_day if row['day']
        }

        if user.role != 'staff':
            expenses_by_day = (
                filter_expenses(params)
                .annotate(day=TruncDate('date'))
                .values('day')
                .annotate(vat_exclusive=Sum('amount_vat_exclusive'), input_vat=Sum('input_vat'))
            )
            for row in expenses_by_day:
                if not row['day']:
                    continue
                entry = trend.setdefault(row['day'], {'date': row['day'], 'revenue': 0})
                entry['expenses'] = (row['vat_exclusive'] or 0) + (row['input_vat'] or 0)

        return sorted(trend.values(), key=lambda entry: entry['date'])

    @staticmethod
    def station_usage(user, params):
        """Sessions, kWh used and revenue per station — bar-chart ready."""
        rows = (
            filter_sessions(user, params)
            .values('station_id', 'station__name')
            .annotate(sessions=Count('id'), kwatt_used=Sum('watt_consumed'), revenue=Sum('total_price'))
            .order_by('-revenue')
        )
        return [
            {
                'station_id': row['station_id'],
                'station_name': row['station__name'],
                'sessions': row['sessions'],
                'kwatt_used': row['kwatt_used'] or 0,
                'revenue': row['revenue'] or 0,
            }
            for row in rows
        ]

    @staticmethod
    def shift_activity(user, params):
        """Shift counts and derived totals per day."""
        rows = (
            filter_shifts(user, params)
            .annotate(day=TruncDate('shift_start'))
            .values('day')
            .annotate(
                shifts=Count('id'),
                earnings=Sum('total_earned_money_on_shift'),
                kwatt_used=Sum('total_kwatt_used_on_shift'),
                cars_charged=Sum('total_car_charged'),
            )
            .order_by('day')
        )
        return [
            {
                'date': row['day'],
                'shifts': row['shifts'],
                'earnings': row['earnings'] or 0,
                'kwatt_used': row['kwatt_used'] or 0,
                'cars_charged': row['cars_charged'] or 0,
            }
            for row in rows
        ]
