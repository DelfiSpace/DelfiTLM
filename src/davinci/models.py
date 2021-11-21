"""
Models for Da Vinci mission.
"""
import datetime
from django.db import models
from ewilgs.models import Downlink

class DaVinci_L0_telemetry(models.Model): #pylint: disable=C0103
    """
    Telemetry Table Delfin3xt
    """
    id = models.ForeignKey(Downlink, editable=False, on_delete=models.DO_NOTHING)
    command_code = models.IntegerField(default=None, null=True)
    content_code = models.IntegerField(default=None, null=True)
    data = models.BinaryField(default=None, null=True)
    received_at = models.TimeField(null=False, default=datetime.time)
