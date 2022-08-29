"""Custom command for populating DelfiC3 buckets.
Run with 'python manage.py adddelfic3data' """
from django.core.management.base import BaseCommand
from transmission.processing.add_dummy_data import add_dummy_tlm_raw_data
from transmission.processing.process_raw_bucket import process_raw_bucket
# pylint: disable=all
class Command(BaseCommand):
    """Django command class"""

    def handle(self, *args, **options):
        """Populate DelfiC3 influxdb buckets"""
        add_dummy_tlm_raw_data("delfi_c3", "delfic3/delfi-c3.txt")
        process_raw_bucket("delfi_c3", "downlink")
