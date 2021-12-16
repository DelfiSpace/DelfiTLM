"""EWILGS models for uplink and downlink data"""
from django.db import models
from django.db.models.deletion import DO_NOTHING
from members.models import Member
import datetime

class Downlink(models.Model):
    """Table for downlink data frames"""
    frame_time = models.TimeField(null=False, default=datetime.time, auto_now=False, auto_now_add=False)
    send_time = models.TimeField(null=False, default=datetime.time, auto_now=False, auto_now_add=False)
    receive_time = models.TimeField(null=False, default=datetime.time, auto_now=False, auto_now_add=False)
    radio_amateur = models.ForeignKey(Member, default=None, null=True, on_delete=DO_NOTHING)
    frame = models.TextField(default=None, null=True)
    frame_binary = models.BinaryField(default=None, null=True)
    version = models.TextField(null=True)
    processed = models.BooleanField(default=False, null=False)
    frequency = models.FloatField(default=None, null=True)
    qos = models.FloatField(default=None, null=True)


class Uplink(models.Model):
    """Table for uplink data frames"""
    UUID_user = models.ForeignKey(Member, editable=False,on_delete=models.CASCADE)
    radio_amateur_username = models.CharField(max_length=70, null=False)
    created_at = models.TimeField(auto_now=False, auto_now_add=False, null=False)
    #auto_now: last edited timestamp is registered
    transmitted_at = models.TimeField(auto_now=False, auto_now_add=False, null=True)
    data = models.BinaryField(null=False)
    frequency = models.FloatField(null=False)
    sat = models.CharField(max_length=70, null=False)
