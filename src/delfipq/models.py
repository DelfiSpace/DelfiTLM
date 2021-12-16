"""
Models for DelfiPQ mission.
"""
from datetime import datetime
from django.db import models
from ewilgs.models import Downlink
from members.models import Member

# pylint: disable=all
class Delfipq_L0_telemetry(models.Model):
    """
    Telemetry Table DelfiPQ
    """
    id = models.OneToOneField(Downlink, primary_key=True, editable=False, on_delete=models.DO_NOTHING)
    frame_time = models.DateTimeField(null=False, default=datetime.now, auto_now=False, auto_now_add=False)
    send_time = models.DateTimeField(null=False, default=datetime.now, auto_now=False, auto_now_add=False)
    receive_time = models.DateTimeField(null=False, default=datetime.now, auto_now=False, auto_now_add=False)
    radio_amateur = models.ForeignKey(Member, to_field="username", db_column="radio_amateur", default=None, null=True, on_delete=models.DO_NOTHING)
    version = models.TextField(null=True)
    processed = models.BooleanField(default=False, null=False)
    frequency = models.FloatField(default=None, null=True)
    qos = models.FloatField(default=None, null=True)
    frame = models.TextField(default=None, null=True)
    frame_binary = models.BinaryField(default=None, null=True)
