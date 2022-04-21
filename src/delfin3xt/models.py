"""
Models for Delft N3xt.
"""
from datetime import datetime
from django.db import models
from transmission.models import Downlink
from members.models import Member

# pylint: disable=all
class Delfin3xt_L0_telemetry(models.Model):
    """
    Telemetry Table DelfiN3xt
    """
    id = models.OneToOneField(Downlink, primary_key=True, editable=False, on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField(null=False, default=datetime.utcnow, auto_now=False, auto_now_add=False)
    radio_amateur = models.ForeignKey(Member, to_field="username", db_column="radio_amateur", default=None, null=True, on_delete=models.DO_NOTHING)
    version = models.TextField(null=True)
    processed = models.BooleanField(default=False, null=False)
    frequency = models.FloatField(default=None, null=True)
    qos = models.FloatField(default=None, null=True)
    frame = models.TextField(default=None, null=True)
    frame_binary = models.BinaryField(default=None, null=True)

