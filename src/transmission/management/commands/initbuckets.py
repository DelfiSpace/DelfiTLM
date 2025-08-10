"""Custom command to initialize influxdb buckets.
Run with 'python manage.py initbuckets' """
from django.core.management.base import BaseCommand
from influxdb_client import BucketRetentionRules
from transmission.processing.satellites import SATELLITES
from transmission.processing.influxdb_api import influxdb_api

class Command(BaseCommand):
    """Django command class"""

    def handle(self, *args, **options):
        """Initialize the database for each satellite, uplink and downlink"""

        db = influxdb_api()
        
        satellites = []
        for sat in SATELLITES:
            satellites.append(sat)

        db.init_database(satellites)
