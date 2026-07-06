from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chargers', '0004_alter_shiftrecord_shift_start'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shiftrecord',
            name='kwh_start',
        ),
        migrations.RemoveField(
            model_name='shiftrecord',
            name='kwh_end',
        ),
        migrations.RemoveField(
            model_name='shiftrecord',
            name='kwh_consumed',
        ),
        migrations.AddField(
            model_name='shiftrecord',
            name='start_kwatts_in_cashpower',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shiftrecord',
            name='addition_kwatt_in_cashpower',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='shiftrecord',
            name='total_kwatt',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='shiftrecord',
            name='total_earned_money_on_shift',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='shiftrecord',
            name='total_kwatt_used_on_shift',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='shiftrecord',
            name='total_car_charged',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shiftrecord',
            name='remaining_cashpower',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='shiftrecord',
            name='money_on_momo',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
