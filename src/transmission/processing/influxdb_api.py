"""Methods for saving raw data frames and retrieving the influxdb API."""
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException
from influxdb_client.domain.bucket import Bucket
from django.conf import settings
from django_logger import logger

RAW_MEASUREMENT = "_raw"
DATETIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%S.%fZ"

class influxdb_api:
    """Class interfcing with InfluxDB"""

    def __init__(self):
        self.url = settings.INFLUXDB['HOST'] + ":" + str(settings.INFLUXDB['PORT'])
        self.token = settings.INFLUXDB['TOKEN']
        self.client = InfluxDBClient(url=self.url, token=self.token)
        self.buckets_api = None
        self.organizations_api = None
        self.write_api = None
        self.query_api = None


    def _get_buckets_api(self):
        if self.buckets_api is None:
            self.buckets_api = self.client.buckets_api()
        return self.buckets_api


    def _get_organizations_api(self):
        if self.organizations_api is None:
            self.organizations_api = self.client.organizations_api()
        return self.organizations_api


    def _get_query_api(self):
        if self.query_api is None:
            self.query_api = self.client.query_api()
        return self.query_api


    def _get_write_api(self):
        if self.write_api is None:
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        return self.write_api


    def init_database(self, satellites):
        """Initialize the database."""

        try:
            orgs = self._get_organizations_api().find_organizations(org="downlink")
        except ApiException:
            self._get_organizations_api().create_organization('downlink')

        try:
            orgs = self._get_organizations_api().find_organizations(org="uplink")
        except ApiException:
            self._get_organizations_api().create_organization('uplink')

        for sat in satellites:
            try:
                self._get_buckets_api().find_buckets(name=sat, org="downlink")
            except ApiException:
                self._get_buckets_api().create_bucket(bucket_name=sat, org="downlink")

            try:
                self._get_buckets_api().find_buckets(name=sat, org="uplink")
            except ApiException:
                self._get_buckets_api().create_bucket(bucket_name=sat, org="uplink")

    def get_last_received_frame(self, satellite: str):
        """Retrieve the last received frame for the specified satellite from the raw
        data bucket."""

        query = f'''from(bucket: "{satellite}")
            |> range(start: 0)
            |> filter(fn: (r) => r["_measurement"] == "{RAW_MEASUREMENT}")
            |> keep(columns: ["_time"])
            |> tail(n: 1)
            '''

        ret = self._get_query_api().query(query=query, org="downlink")

        if len(ret) > 0:
            # data received found in bucket
            return ret[0].records[0]["_time"]

        # no result found
        return None


    def get_raw_frames_to_process(self, satellite: str, link: str, frames: int = 100):
        """Retrieve the first raw frames to process"""

        get_frames_to_process = f'''
            from(bucket: "{satellite}")
            |> range(start: 0, stop: now())
            |> filter(fn: (r) => r._measurement == "{RAW_MEASUREMENT}")
            |> filter(fn: (r) => r["_field"] == "processed" or
                r["_field"] == "frame" or
                r["_field"] == "user")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> filter(fn: (r) => r[\"processed\"] == false)
            |> sort(columns: ["_time"], desc: false)  
            |> limit(n:{frames}, offset: 0)'''

        # query result as dataframe
        dataframe = self._get_query_api().query_data_frame(query=get_frames_to_process, org=link)
        return dataframe


    def save_raw_frame(self, satellite: str, link: str, timestamp: datetime, tlm: dict) -> bool:
        """Write frame to corresponding satellite table (if not already stored).
        Returns True if the frame was stored and False otherwise (if the frame is already stored).
        Also store the frame with processed = False."""

        time_range_start = (timestamp - timedelta(seconds=0.1)).strftime(DATETIME_FORMAT_STRING)
        time_range_stop = (timestamp + timedelta(seconds=0.1)).strftime(DATETIME_FORMAT_STRING)

        # check if frame already exists
        query = f'''from(bucket: "{satellite}")
            |> range(start: {time_range_start}, stop: {time_range_stop})
            |> filter(fn: (r) => r._measurement == "{RAW_MEASUREMENT}")
            |> filter(fn: (r) => r["_field"] == "frame" and r["_value"] == "{tlm["frame"]}")
            '''

        # store frame only if not stored already
        if len(self._get_query_api().query(query=query, org=link)) != 0:
            return False

        tlm["processed"] = False
        tlm["invalid"] = False

        db_fields = {
            "measurement": RAW_MEASUREMENT,
            "time": timestamp,
            "tags": {},
            "fields": tlm
        }

        self._get_write_api().write(satellite, link, db_fields)

        return True


    def save_processed_frame(self, satellite: str, link: str, measurement: str, timestamp, tags, fields):
        """Write frame to corresponding satellite table (if not already stored).
        Returns True if the frame was stored and False otherwise (if the frame is already stored).
        Also store the frame with processed = False."""

        #time_range_lower_bound = (timestamp - timedelta(seconds=1)).strftime(DATETIME_FORMAT_STRING)
        #time_range_upper_bound = (timestamp + timedelta(seconds=1)).strftime(DATETIME_FORMAT_STRING)

        # check if frame already exists
        #query = f'''from(bucket: "{satellite}")
        #    |> range(start: {time_range_lower_bound}, stop: {time_range_upper_bound})
        #    |> filter(fn: (r) => r._measurement == "raw")
        #    |> filter(fn: (r) => r["_field"] == "frame" and r["_value"] == "{tlm["frame"]}")
        #    '''
        # store frame only if not stored already
        #if len(self._get_query_api().query(query=query)) != 0:
        #    logger.info("Found!")
        #    return False

        #tlm["processed"] = False
        #tlm["invalid"] = False

        db_fields = {
            "measurement": measurement,
            "time": timestamp,
            "tags": tags,
            "fields": fields
        }

        self._get_write_api().write(satellite, link, db_fields)


    def update_raw_frame(self, satellite: str, link: str, timestamp: datetime, tlm: dict) -> bool:
        """Updates frame in corresponding satellite table (if not already stored).
        Returns True if the frame was updated and False otherwise (if the frame was not found).
        """
        time_range_start = (timestamp - timedelta(seconds=0.1)).strftime(DATETIME_FORMAT_STRING)
        time_range_stop = (timestamp + timedelta(seconds=0.1)).strftime(DATETIME_FORMAT_STRING)

        # check if frame already exists
        query = f'''from(bucket: "{satellite}")
            |> range(start: {time_range_start}, stop: {time_range_stop})
            |> filter(fn: (r) => r._measurement == "{RAW_MEASUREMENT}")
            '''

        # update frame only if already present
        if len(self._get_query_api().query(query=query, org=link)) != 0:
            bucket = satellite

            db_fields = {
                "measurement": RAW_MEASUREMENT,
                "time": timestamp,
                "tags": {},
                "fields": tlm
            }

            self._get_write_api().write(bucket, link, db_fields)
            return True

        return False
