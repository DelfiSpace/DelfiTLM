# Generated by Django 3.2.8 on 2021-12-16 14:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('delfin3xt', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='delfin3xt_l0_telemetry',
            name='radio_amateur',
            field=models.ForeignKey(db_column='radio_amateur', default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, to_field='username'),
        ),
    ]
