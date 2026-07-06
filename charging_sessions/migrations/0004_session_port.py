from django.db import migrations, models
import django.db.models.query_utils


class Migration(migrations.Migration):

    dependencies = [
        ('charging_sessions', '0003_session_shift_and_percentages'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargingsession',
            name='port',
            field=models.PositiveSmallIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name='chargingsession',
            constraint=models.UniqueConstraint(
                condition=django.db.models.query_utils.Q(('ended_at__isnull', True)),
                fields=('charger', 'port'),
                name='unique_active_session_per_charger_port',
            ),
        ),
    ]
