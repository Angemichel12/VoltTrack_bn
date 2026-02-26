from django.db import models


class Station(models.Model):
    name = models.CharField(max_length=255)
    price_per_watt = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stations'

    def __str__(self):
        return self.name