# Generated by Django 3.2.8 on 2021-12-12 19:55

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ewilgs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DaVinci_L0_telemetry',
            fields=[
                ('id', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='ewilgs.downlink')),
                ('command_code', models.IntegerField(default=None, null=True)),
                ('content_code', models.IntegerField(default=None, null=True)),
                ('data', models.BinaryField(default=None, null=True)),
                ('received_at', models.TimeField(default=datetime.time)),
            ],
        ),
    ]