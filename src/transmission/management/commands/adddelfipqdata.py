"""Custom command for populating DelfiPq buckets.
Run with 'python manage.py adddelfipqdata' """
from django.core.management.base import BaseCommand
from delfipq.add_dummy_data import delfi_pq_add_dummy_tlm_raw_data
from delfipq.process_raw_telemetry import process_frames_delfi_pq

class Command(BaseCommand):
    """Django command class"""

    def handle(self, *args, **options):
        """Populate DelfiPQ influxdb buckets"""
        delfi_pq_add_dummy_tlm_raw_data()
        process_frames_delfi_pq("downlink")
