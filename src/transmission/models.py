"""Models for uplink and downlink data"""
from django.db import models
from django.db.models.deletion import DO_NOTHING
from django.utils import timezone


class Satellite(models.Model):
    """Table containing all satellites managed in this db"""
    sat = models.CharField(null=False, max_length=32, unique=True)
    norad_id = models.IntegerField(null=True, unique=True)
    status = models.SlugField

    def __str__(self) -> str:
        return str(self.sat)


class TLE(models.Model):
    """Table for satellite TLEs history"""
    valid_from = models.DateTimeField(null=True, auto_now=False, auto_now_add=False)
    sat = models.ForeignKey(Satellite, to_field="sat", db_column="sat", null=False, on_delete=DO_NOTHING)
    tle = models.TextField(null=False)


class Downlink(models.Model):
    """Table for downlink data frames"""
    timestamp = models.DateTimeField(null=False, default=timezone.now, auto_now=False, auto_now_add=False)
    observer = models.CharField(null=False, max_length=128)
    application = models.TextField(null=True, blank=True)
    processed = models.BooleanField(default=False, null=False)
    invalid = models.BooleanField(null=True, blank=True)
    frequency = models.FloatField(null=True, blank=True)
    frame = models.TextField(default=None, null=False)
    metadata = models.JSONField(null=True, blank=True)

    def to_dictionary(self) -> dict:
        """Convert Downlink object to dict"""
        frame_dict = {}
        frame_dict["user"] = self.observer
        frame_dict["application"] = self.application
        frame_dict["processed"] = self.processed
        frame_dict["invalid"] = self.invalid
        frame_dict["frequency"] = self.frequency
        frame_dict["frame"] = self.frame
        frame_dict["metadata"] = self.metadata

        return frame_dict


class Uplink(models.Model):
    """Table for uplink data frames"""
    timestamp = models.DateTimeField(null=False, default=timezone.now, auto_now=False, auto_now_add=False)
    operator = models.CharField(null=False, max_length=128)
    application = models.TextField(null=True, blank=True)
    processed = models.BooleanField(default=False, null=False)
    invalid = models.BooleanField(null=True, blank=True)
    frequency = models.FloatField(null=False)
    frame = models.TextField(default=None, null=False)
    metadata = models.JSONField(null=True, blank=True)

    def to_dictionary(self) -> dict:
        """Convert Uplink object to dict"""
        frame_dict = {}
        frame_dict["user"] = self.operator
        frame_dict["application"] = self.application
        frame_dict["processed"] = self.processed
        frame_dict["invalid"] = self.invalid
        frame_dict["frequency"] = self.frequency
        frame_dict["frame"] = self.frame
        frame_dict["metadata"] = self.metadata

        return frame_dict

#class DateTimeMicrosecondsField(models.DateTimeField):
#    def db_type(self, connection):
#        return "timestamp(6) with time zone"
#
#    #def rel_db_type(self, connection):
#    #    return "integer UNSIGNED"
