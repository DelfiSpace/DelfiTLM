"""
Models for Da Vinci mission.
"""
from datetime import datetime
from django.db import models
from transmission.models import Downlink
from members.models import Member

#pylint: disable=all
class DaVinci_L0_telemetry(models.Model):
    """
    Telemetry Table Da Vinci
    """
    id = models.OneToOneField(Downlink, primary_key=True, editable=False, on_delete=models.DO_NOTHING)
    command_code = models.IntegerField(default=None, null=True)
    content_code = models.IntegerField(default=None, null=True)
    timestamp = models.DateTimeField(null=False, default=datetime.utcnow, auto_now=False, auto_now_add=False)
    radio_amateur = models.ForeignKey(Member, to_field="username", db_column="radio_amateur", default=None, null=True, on_delete=models.DO_NOTHING)
    version = models.TextField(null=True)
    processed = models.BooleanField(default=False, null=False)
    frequency = models.FloatField(default=None, null=True)
    qos = models.FloatField(default=None, null=True)
    frame = models.TextField(default=None, null=True)
    frame_binary = models.BinaryField(default=None, null=True)
