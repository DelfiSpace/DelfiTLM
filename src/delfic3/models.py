"""
Models for Delfic3 mission.
"""
import datetime
from django.db import models
from ewilgs.models import Downlink

class Delfic3_L0_telemetry(models.Model): #pylint: disable=C0103
    """
    Telemetry Table Delfic3
    """
    id = models.ForeignKey(Downlink, primary_key=True, editable=False, on_delete=models.DO_NOTHING)
    frame_time = models.IntegerField(default=None, null=True)
    send_time = models.IntegerField(default=None, null=True)
    receive_time = models.TimeField(null=False, default = datetime.time )
    radio_amateur = models.IntegerField(default=None, null=True)
    frame = models.BinaryField(default=None, null=True)
    version = models.TextField
    processed = models.BooleanField(default=False, null=False)
    frequency = models.FloatField(default=None, null=True)
    qos = models.FloatField(default=None, null=True)
