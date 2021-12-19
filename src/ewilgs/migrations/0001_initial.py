# Generated by Django 3.2.8 on 2021-12-19 02:36

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Downlink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('frame_time', models.DateTimeField(default=datetime.datetime.now)),
                ('send_time', models.DateTimeField(default=datetime.datetime.now)),
                ('receive_time', models.DateTimeField(default=datetime.datetime.now)),
                ('version', models.TextField(null=True)),
                ('processed', models.BooleanField(default=False)),
                ('frequency', models.FloatField(default=None, null=True)),
                ('qos', models.FloatField(default=None, null=True)),
                ('frame', models.TextField(default=None, null=True)),
                ('frame_binary', models.BinaryField(default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Uplink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('frame_time', models.DateTimeField(default=datetime.datetime.now)),
                ('send_time', models.DateTimeField(default=datetime.datetime.now)),
                ('frequency', models.FloatField()),
                ('qos', models.FloatField(default=None, null=True)),
                ('sat', models.CharField(max_length=70)),
                ('frame', models.TextField(default=None, null=True)),
                ('frame_binary', models.BinaryField(default=None, null=True)),
            ],
        ),
    ]
