# Generated by Django 3.2.8 on 2021-12-16 16:06

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ewilgs', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uplink',
            name='UUID_user',
        ),
        migrations.RemoveField(
            model_name='uplink',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='uplink',
            name='data',
        ),
        migrations.RemoveField(
            model_name='uplink',
            name='radio_amateur_username',
        ),
        migrations.RemoveField(
            model_name='uplink',
            name='transmitted_at',
        ),
        migrations.AddField(
            model_name='uplink',
            name='frame',
            field=models.TextField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='uplink',
            name='frame_binary',
            field=models.BinaryField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='uplink',
            name='frame_time',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='uplink',
            name='qos',
            field=models.FloatField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='uplink',
            name='radio_amateur',
            field=models.ForeignKey(db_column='radio_amateur', default=5, on_delete=django.db.models.deletion.DO_NOTHING, to='members.member', to_field='username'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='uplink',
            name='send_time',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
