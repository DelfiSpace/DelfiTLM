"""EWILGS models for uplink and downlink data"""
from django.db import models
from django.db.models.deletion import DO_NOTHING
from django.utils import timezone
from members.models import Member

#pylint: disable=all
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
    frame = models.TextField(default=None, null=True)
    frame_binary = models.BinaryField(default=None, null=True)


class Uplink(models.Model):
    """Table for uplink data frames"""
    radio_amateur = models.ForeignKey(Member, to_field="username", db_column="radio_amateur", null=False, on_delete=DO_NOTHING)
    frame_time = models.DateTimeField(null=False, default=timezone.now, auto_now=False, auto_now_add=False)
    send_time = models.DateTimeField(null=False, default=timezone.now, auto_now=False, auto_now_add=False)
    frequency = models.FloatField(null=False)
    qos = models.FloatField(default=None, null=True)
    sat = models.CharField(max_length=70, null=False)
    frame = models.TextField(default=None, null=True)
    frame_binary = models.BinaryField(default=None, null=True)

