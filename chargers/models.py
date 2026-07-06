from django.db import models
from django.utils import timezone


class Charger(models.Model):
    PORT_LEFT = 'left'
    PORT_RIGHT = 'right'
    PORT_CHOICES = [(PORT_LEFT, 'Left'), (PORT_RIGHT, 'Right')]
    PORTS = [PORT_LEFT, PORT_RIGHT]  # every charger has a left and a right port; each charges one car independently

    name = models.CharField(max_length=255)
    station = models.ForeignKey(
        'stations.Station',
        on_delete=models.CASCADE,
        related_name='chargers',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chargers'

    def __str__(self):
        return f"{self.name} @ {self.station.name}"


class ShiftRecord(models.Model):
    station = models.ForeignKey(
        'stations.Station',
        on_delete=models.CASCADE,
        related_name='shift_records',
        db_index=True
    )
    staff = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='shift_records',
        limit_choices_to={'role': 'staff'}
    )
    shift_start = models.DateTimeField(default=timezone.now)
    shift_end = models.DateTimeField(null=True, blank=True)

    # CashPower balance for the shift
    start_kwatts_in_cashpower = models.DecimalField(max_digits=10, decimal_places=2)
    addition_kwatt_in_cashpower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_kwatt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Computed when the shift is closed, from the ChargingSessions linked to it
    total_earned_money_on_shift = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_kwatt_used_on_shift = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_car_charged = models.PositiveIntegerField(null=True, blank=True)

    # Entered by the staff member when closing the shift (actual meter reading, not computed)
    money_on_momo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    end_kwatts_in_cashpower = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shift_records'
        ordering = ['-shift_start']

    @classmethod
    def get_open_for(cls, staff):
        return cls.objects.filter(staff=staff, shift_end__isnull=True).select_related('station').first()

    def add_cashpower(self, amount):
        self.addition_kwatt_in_cashpower += amount
        self.save(update_fields=['addition_kwatt_in_cashpower', 'updated_at'])

    def close_shift(self, money_on_momo, end_kwatts_in_cashpower, shift_end=None):
        from django.db.models import Sum, Count

        totals = self.sessions.aggregate(
            earned=Sum('total_price'),
            kwatt_used=Sum('watt_consumed'),
            cars=Count('id'),
        )

        self.total_kwatt = self.start_kwatts_in_cashpower + self.addition_kwatt_in_cashpower
        self.total_earned_money_on_shift = totals['earned'] or 0
        self.total_kwatt_used_on_shift = totals['kwatt_used'] or 0
        self.total_car_charged = totals['cars'] or 0
        self.money_on_momo = money_on_momo
        self.end_kwatts_in_cashpower = end_kwatts_in_cashpower
        self.shift_end = shift_end or timezone.now()
        self.save(update_fields=[
            'total_kwatt', 'total_earned_money_on_shift', 'total_kwatt_used_on_shift',
            'total_car_charged', 'money_on_momo', 'end_kwatts_in_cashpower', 'shift_end',
            'notes', 'updated_at',
        ])

    def __str__(self):
        return f"{self.staff} | {self.station} | {self.shift_start:%Y-%m-%d %H:%M}"