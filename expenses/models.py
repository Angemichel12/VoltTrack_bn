from django.db import models


class Expense(models.Model):
    station = models.ForeignKey(
        'stations.Station',
        on_delete=models.CASCADE,
        related_name='expenses',
        db_index=True
    )
    description = models.TextField()
    amount_vat_exclusive = models.DecimalField(max_digits=12, decimal_places=2)
    input_vat = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'expenses'
        ordering = ['-date']

    def __str__(self):
        return f"{self.station.name} | {self.description[:40]} | {self.date:%Y-%m-%d}"
