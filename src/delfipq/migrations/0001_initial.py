# Generated by Django 3.2.12 on 2022-04-21 09:59

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('transmission', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Delfipq_L0_telemetry',
            fields=[
                ('id', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='transmission.downlink')),
                ('timestamp', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('version', models.TextField(null=True)),
                ('processed', models.BooleanField(default=False)),
                ('frequency', models.FloatField(default=None, null=True)),
                ('qos', models.FloatField(default=None, null=True)),
                ('frame', models.TextField(default=None, null=True)),
                ('frame_binary', models.BinaryField(default=None, null=True)),
                ('radio_amateur', models.ForeignKey(db_column='radio_amateur', default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
        ),
    ]
