"""Custom command to initialize influxdb buckets.
Run with 'python manage.py initbuckets' """
from django.core.management.base import BaseCommand
from influxdb_client import BucketRetentionRules
from transmission.telemetry_scraper import SATELLITES, get_influxdb_bucket_api

class Command(BaseCommand):
    """Django command class"""

    def handle(self, *args, **options):
        """Create influxdb buckets for each satellite:
         - 1 raw data bucket
         - 1 bucket for uplink data
         - 1 bucket for downlink data"""

        buckets_api = get_influxdb_bucket_api()
        buckets = []
        for sat in SATELLITES:
            buckets.append(sat + "_raw_data")
            buckets.append(sat + "_downlink")
            buckets.append(sat + "_uplink")

        for bucket in buckets:
            retention_rules = BucketRetentionRules(type="expire", every_seconds=0)
            if buckets_api.find_bucket_by_name(bucket) is None:
                buckets_api.create_bucket(bucket_name=bucket, retention_rules=retention_rules)
                print(f"Bucket: {bucket} created")
