import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('charging_sessions', '0002_initial'),
        ('chargers', '0005_shiftrecord_cashpower_redesign'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargingsession',
            name='shift',
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sessions',
                to='chargers.shiftrecord',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='chargingsession',
            name='starting_car_percentage',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chargingsession',
            name='ending_car_percentage',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
