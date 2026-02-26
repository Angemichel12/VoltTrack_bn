from django.db import models


class Charger(models.Model):
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
    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField(null=True, blank=True)
    kwh_start = models.DecimalField(max_digits=10, decimal_places=2)
    kwh_end = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    kwh_consumed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shift_records'
        ordering = ['-shift_start']

    def close_shift(self, kwh_end: float, shift_end=None):
        from django.utils import timezone
        self.kwh_end = kwh_end
        self.kwh_consumed = round(float(kwh_end) - float(self.kwh_start), 2)
        self.shift_end = shift_end or timezone.now()
        self.save(update_fields=['kwh_end', 'kwh_consumed', 'shift_end', 'updated_at'])

    def __str__(self):
        return f"{self.staff} | {self.station} | {self.shift_start:%Y-%m-%d %H:%M}"