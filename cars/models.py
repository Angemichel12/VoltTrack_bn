from django.db import models
from django.utils import timezone


class Car(models.Model):
    plate_number = models.CharField(max_length=50, unique=True, db_index=True)
    owner_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    unique_price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    # When True, this car charges on credit and settles its accumulated balance
    # later, instead of paying per charge. Admin-only field.
    is_postpaid = models.BooleanField(default=False)
    optional_info = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cars'

    def __str__(self):
        return self.plate_number


class CarPayment(models.Model):
    """A settlement event: an admin records money paid by a (postpaid) car
    against its accumulated unpaid charging sessions."""
    car = models.ForeignKey(
        'cars.Car',
        on_delete=models.PROTECT,
        related_name='payments',
        db_index=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='car_payments',
    )
    paid_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'car_payments'
        ordering = ['-paid_at']

    def __str__(self):
        return f"Payment {self.amount} for {self.car.plate_number}"