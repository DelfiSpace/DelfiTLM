from django.db import models
from members.models import Members

class Downlink(models.Model):
    received_at = models.TimeField(auto_now_add=True, null=False)
    data = models.BinaryField(null=False)
    frequency = models.FloatField(null=False)
    processed = models.BooleanField(null=True) #NULL values are allowed for this field

class Uplink(models.Model):
    UUID_user = models.ForeignKey(Members, editable=False,on_delete=models.CASCADE)
    created_at = models.TimeField(auto_now=False, auto_now_add=False, null=False)
    transmitted_at = models.TimeField(auto_now=False, auto_now_add=False, null=True) #auto_now: last edited timestamp is registered
    data = models.BooleanField(null=True)
    frequency = models.FloatField(null=False)
    radio_amateur_username = models.CharField(max_length=70, null=False)
    sat = models.CharField(max_length=70, null=False)
