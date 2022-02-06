"""EWILGS models for uplink and downlink data"""
from django.db import models
from django.db.models.deletion import DO_NOTHING
from django.utils import timezone
from members.models import Member

#pylint: disable=all

class Satellite(models.Model):
    """Table contaning all satellites managed in this db"""
    sat = models.CharField(null=False, max_length=70, unique=True)

    def __str__(self) -> str:
        return self.sat


class Downlink(models.Model):
    """Table for downlink data frames"""
    frame_time = models.DateTimeField(null=False, default=timezone.now, auto_now=False, auto_now_add=False)
    send_time = models.DateTimeField(null=False, default=timezone.now, auto_now=False, auto_now_add=False)
    receive_time = models.DateTimeField(null=False, default=timezone.now, auto_now=False, auto_now_add=False)
    radio_amateur = models.ForeignKey(Member, to_field="username", db_column="radio_amateur", default=None, null=True, on_delete=DO_NOTHING)
    version = models.TextField(null=True)
    processed = models.BooleanField(default=False, null=False)
    frequency = models.FloatField(default=None, null=True)
    qos = models.FloatField(default=None, null=True)
    sat = models.ForeignKey(Satellite, to_field="sat", db_column="sat", null=True, on_delete=DO_NOTHING)
    frame = models.TextField(default=None, null=True)
    frame_binary = models.BinaryField(default=None, null=True)


class Uplink(models.Model):
    """Table for uplink data frames"""
    radio_amateur = models.ForeignKey(Member, to_field="username", db_column="radio_amateur", null=False, on_delete=DO_NOTHING)
    frame_time = models.DateTimeField(null=False, default=timezone.now, auto_now=False, auto_now_add=False)
    send_time = models.DateTimeField(null=False, default=timezone.now, auto_now=False, auto_now_add=False)
    frequency = models.FloatField(null=False)
    qos = models.FloatField(default=None, null=True)
    sat = models.ForeignKey(Satellite, to_field="sat", db_column="sat", null=False, on_delete=DO_NOTHING)
    frame = models.TextField(default=None, null=True)
    frame_binary = models.BinaryField(default=None, null=True)


class TLE(models.Model):
    """Table for satellite TLEs history"""
    valid_from = models.DateTimeField(null=True, auto_now=False, auto_now_add=False)
    sat = models.ForeignKey(Satellite, to_field="sat", db_column="sat", null=False, on_delete=DO_NOTHING)
    tle = models.TextField(null=False)
