import datetime

from django.db import models

class Delfin3xt_L0_telemetry(models.Model):
    counter = models.PositiveIntegerField(primary_key=True, null=False)
    frame_time = models.IntegerField(default=None, null=True)
    send_time = models.IntegerField(default=None, null=True)
    receive_time = models.TimeField(auto_now_add=True, null=False, default = datetime.time )
    radio_amateur = models.IntegerField(default=None, null=True)
    frame = models.BinaryField(default=None, null=True)
    version = models.TextField
    processed = models.BooleanField(default=False, null=False)
    frequency = models.FloatField(default=None, null=True)
    qos = models.FloatField(default=None, null=True)
