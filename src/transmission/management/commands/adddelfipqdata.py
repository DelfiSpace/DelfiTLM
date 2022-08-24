"""Custom command for populating DelfiPQ buckets.
Run with 'python manage.py adddelfipqdata' """
from django.core.management.base import BaseCommand
from delfipq.add_dummy_data import delfi_pq_add_dummy_tlm_raw_data
from transmission.processing.process_raw_bucket import process_raw_bucket

class Command(BaseCommand):
    """Django command class"""

    def handle(self, *args, **options):
        """Populate DelfiPQ influxdb buckets"""
        delfi_pq_add_dummy_tlm_raw_data()
        process_raw_bucket("delfi_pq", "downlink")
