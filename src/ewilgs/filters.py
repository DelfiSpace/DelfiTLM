"""Telemetry filters"""
import django_filters
from .models import Downlink, Uplink

class TelemetryDownlinkFilter(django_filters.FilterSet):
    """Filter downlink telemetry by frame date interval, frequency and qos ranges"""
    frame_date = django_filters.DateFromToRangeFilter(field_name="frame_time")
    frequency = django_filters.RangeFilter(field_name="frequency")
    qos = django_filters.RangeFilter(field_name="qos")
    class Meta:
        """Meta class to specify model"""
        model = Downlink
        fields = ["processed", "radio_amateur"]

class TelemetryUplinkFilter(django_filters.FilterSet):
    """Filter uplink telemetry by frame date interval, frequency and qos ranges"""
    frame_date = django_filters.DateFromToRangeFilter(field_name="frame_time")
    frequency = django_filters.RangeFilter(field_name="frequency")
    qos = django_filters.RangeFilter(field_name="qos")
    class Meta:
        """Meta class to specify model"""
        model = Uplink
        fields = ["radio_amateur"]
