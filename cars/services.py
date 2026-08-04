from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, Count

from charging_sessions.models import ChargingSession
from .models import CarPayment


class CarPaymentService:
    """Per-car credit ledger: balances and FIFO settlement for postpaid cars.

    A car's charging sessions each carry `total_price` and `amount_paid`.
    Prepaid cars are settled automatically at charge time; postpaid cars
    accumulate a debt that an admin settles later by recording payments here.
    """

    @staticmethod
    def get_balance(car):
        totals = ChargingSession.objects.filter(
            car=car, total_price__isnull=False
        ).aggregate(
            times_charged=Count('id'),
            total_charged=Sum('total_price'),
            total_paid=Sum('amount_paid'),
        )
        total_charged = totals['total_charged'] or Decimal('0')
        total_paid = totals['total_paid'] or Decimal('0')
        return {
            'car_id': car.id,
            'plate_number': car.plate_number,
            'is_postpaid': car.is_postpaid,
            'times_charged': totals['times_charged'] or 0,
            'total_charged': total_charged,
            'total_paid': total_paid,
            'outstanding': total_charged - total_paid,
            'times_paid': car.payments.count(),
        }

    @staticmethod
    @transaction.atomic
    def record_payment(car, amount, recorded_by, note=''):
        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        balance = CarPaymentService.get_balance(car)
        outstanding = balance['outstanding']
        if amount > outstanding:
            raise ValueError(f"Payment exceeds outstanding balance of {outstanding}.")

        payment = CarPayment.objects.create(
            car=car,
            amount=amount,
            recorded_by=recorded_by,
            note=note or '',
        )

        # FIFO: settle the oldest unpaid sessions first.
        remaining = amount
        unpaid_sessions = (
            ChargingSession.objects
            .select_for_update()
            .filter(car=car, is_paid=False, total_price__isnull=False)
            .order_by('started_at')
        )
        for session in unpaid_sessions:
            if remaining <= 0:
                break
            due = session.total_price - session.amount_paid
            if due <= 0:
                continue
            applied = min(remaining, due)
            session.amount_paid += applied
            if session.amount_paid >= session.total_price:
                session.is_paid = True
            session.save(update_fields=['amount_paid', 'is_paid'])
            remaining -= applied

        return payment, CarPaymentService.get_balance(car)
