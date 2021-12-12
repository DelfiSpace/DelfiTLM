"""
Models for Da Vinci mission.
"""
import datetime
from django.db import models
from ewilgs.models import Downlink

class DaVinci_L0_telemetry(models.Model): #pylint: disable=C0103
    """
    Telemetry Table Da Vinci
    """
    id = models.OneToOneField(Downlink, primary_key=True, editable=False, on_delete=models.DO_NOTHING)   #pylint: disable=C0301
    command_code = models.IntegerField(default=None, null=True)
    content_code = models.IntegerField(default=None, null=True)
    data = models.BinaryField(default=None, null=True)
    received_at = models.TimeField(null=False, auto_now=False, auto_now_add=False, default=datetime.time) #pylint: disable=C0301
