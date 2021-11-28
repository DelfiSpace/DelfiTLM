"""
Models for Delft N3xt.
"""
import datetime
from django.db import models
from ewilgs.models import Downlink

class Delfin3xt_L0_telemetry(models.Model): #pylint: disable=C0103
    """
    Telemetry Table Delfin3xt
    """
    id = models.ForeignKey(Downlink, primary_key=True, editable=False, on_delete=models.DO_NOTHING)
    frame_time = models.TimeField(null=False, default=datetime.time, auto_now=False, auto_now_add=False) #pylint: disable=C0301
    send_time = models.TimeField(null=False, default=datetime.time, auto_now=False, auto_now_add=False) #pylint: disable=C0301
    receive_time = models.TimeField(null=False, default=datetime.time, auto_now=False, auto_now_add=False) #pylint: disable=C0301
    radio_amateur = models.IntegerField(default=None, null=True)
    frame = models.BinaryField(default=None, null=True)
    version = models.TextField
    processed = models.BooleanField(default=False, null=False)
    frequency = models.FloatField(default=None, null=True)
    qos = models.FloatField(default=None, null=True)
