"""
Models for Da Vinci mission.
"""
import datetime
from django.db import models
from ewilgs.models import Downlink

#pylint: disable=all
class DaVinci_L0_telemetry(models.Model):
    """
    Telemetry Table Da Vinci
    """
    id = models.OneToOneField(Downlink, primary_key=True, editable=False, on_delete=models.DO_NOTHING)
    command_code = models.IntegerField(default=None, null=True)
    content_code = models.IntegerField(default=None, null=True)
    frame_time = models.TimeField(null=False, default=datetime.time, auto_now=False, auto_now_add=False)
    send_time = models.TimeField(null=False, default=datetime.time, auto_now=False, auto_now_add=False)
    receive_time = models.TimeField(null=False, default=datetime.time, auto_now=False, auto_now_add=False)
    radio_amateur = models.IntegerField(default=None, null=True)
    frame = models.BinaryField(default=None, null=True)
    version = models.TextField(null=True)
    processed = models.BooleanField(default=False, null=False)
    frequency = models.FloatField(default=None, null=True)
    qos = models.FloatField(default=None, null=True)
