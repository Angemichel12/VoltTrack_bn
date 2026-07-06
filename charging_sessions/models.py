from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from chargers.models import Charger


class ChargingSession(models.Model):
    station = models.ForeignKey(
        'stations.Station',
        on_delete=models.PROTECT,
        related_name='sessions',
        db_index=True
    )
    charger = models.ForeignKey(
        'chargers.Charger',
        on_delete=models.PROTECT,
        related_name='sessions',
        db_index=True
    )
    port = models.CharField(max_length=5, choices=Charger.PORT_CHOICES)
    staff = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='sessions',
        db_index=True
    )
    car = models.ForeignKey(
        'cars.Car',
        on_delete=models.PROTECT,
        related_name='sessions',
        db_index=True
    )
    shift = models.ForeignKey(
        'chargers.ShiftRecord',
        on_delete=models.PROTECT,
        related_name='sessions',
        db_index=True
    )
    starting_car_percentage = models.PositiveSmallIntegerField(null=True, blank=True)
    ending_car_percentage = models.PositiveSmallIntegerField(null=True, blank=True)
    watt_consumed = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'charging_sessions'
        constraints = [
            models.UniqueConstraint(
                fields=['charger', 'port'],
                condition=Q(ended_at__isnull=True),
                name='unique_active_session_per_charger_port',
            )
        ]

    def save(self, *args, **kwargs):
        if self.watt_consumed:
            price_per_watt = self.car.unique_price or self.station.price_per_watt
            if price_per_watt:
                self.total_price = self.watt_consumed * price_per_watt
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.ended_at is None

    @property
    def duration(self):
        if not self.ended_at:
            return None
        return self.ended_at - self.started_at

    def __str__(self):
        return f"Session {self.id} - {self.car.plate_number}"