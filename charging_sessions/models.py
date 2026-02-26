from django.db import models
from django.core.exceptions import ValidationError


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
    watt_consumed = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'charging_sessions'

    def save(self, *args, **kwargs):
        if self.watt_consumed and self.station.price_per_watt:
            self.total_price = self.watt_consumed * self.station.price_per_watt
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.ended_at is None

    def __str__(self):
        return f"Session {self.id} - {self.car.plate_number}"