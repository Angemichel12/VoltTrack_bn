from django.db import models


class Car(models.Model):
    plate_number = models.CharField(max_length=50, unique=True, db_index=True)
    optional_info = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cars'

    def __str__(self):
        return self.plate_number