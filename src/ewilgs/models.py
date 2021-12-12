"""EWILGS models for uplink and downlink data"""
from django.db import models
from members.models import Member

class Downlink(models.Model):
    """Table for downlink data frames"""
    received_at = models.TimeField(auto_now_add=False, null=False)
    data = models.BinaryField(null=False)
    frequency = models.FloatField(null=False)
    processed = models.BooleanField(null=True) #NULL values are allowed for this field

class Uplink(models.Model):
    """Table for uplink data frames"""
    UUID_user = models.ForeignKey(Member, editable=False,on_delete=models.CASCADE)
    radio_amateur_username = models.CharField(max_length=70, null=False)
    created_at = models.TimeField(auto_now=False, auto_now_add=False, null=False)
    #auto_now: last edited timestamp is registered
    transmitted_at = models.TimeField(auto_now=False, auto_now_add=False, null=True)
    data = models.BinaryField(null=False)
    frequency = models.FloatField(null=False)
    sat = models.CharField(max_length=70, null=False)
