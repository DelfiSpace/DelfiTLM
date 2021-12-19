# Generated by Django 3.2.8 on 2021-12-19 02:53

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delfic3', '0002_delfic3_l0_telemetry_radio_amateur'),
    ]

    operations = [
        migrations.AlterField(
            model_name='delfic3_l0_telemetry',
            name='frame_time',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
        migrations.AlterField(
            model_name='delfic3_l0_telemetry',
            name='receive_time',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
        migrations.AlterField(
            model_name='delfic3_l0_telemetry',
            name='send_time',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
    ]
