"""Methods for saving raw data frames and retrieving the influxdb API."""
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from django_logger import logger
from django.conf import settings

from transmission.processing.satellites import TIME_FORMAT


class influxdb_api:
    def __init__(self):
        self.url = settings.INFLUXDB['HOST'] + ":" + str(settings.INFLUXDB['PORT'])
        self.token = settings.INFLUXDB['TOKEN']
        self.organization = settings.INFLUXDB['ORGANIZATION']
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.organization)
        self.buckets_api = None
        self.write_api = None
        self.query_api = None


    def _get_buckets_api(self):
        if self.buckets_api is None:
            self.buckets_api = self.client.buckets_api()
        return self.buckets_api


    def _get_query_api(self):
        if self.query_api is None:
            self.query_api = self.client.query_api()
        return self.query_api


    def _get_write_api(self):
        if self.write_api is None:
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        return self.write_api


    def get_last_received_frame(self, satellite: str):
        """Retrieve the last received frame for the specified satellite from the raw
        data bucket."""

        bucket = satellite + "_raw_data"

        query = f'''from(bucket: "{bucket}")
            |> range(start: 0)
            |> filter(fn: (r) => r["_measurement"] == "raw")
            |> keep(columns: ["_time"])
            |> tail(n: 1)
            '''

        ret = self._get_query_api().query(query=query)

        if len(ret) > 0:
            # data received found in bucket
            return ret[0].records[0]["_time"]

        # no result found
        return None


    def get_raw_frames_to_process(self, satellite: str, link: str, frames: int = 100):
        """Retrieve the first raw frames to process"""

        bucket = satellite + "_raw_data"

        get_frames_to_process = f'''
            from(bucket: "{bucket}")
            |> range(start: 0, stop: now())
            |> filter(fn: (r) => r._measurement == "raw")
            |> filter(fn: (r) => r["_field"] == "processed" or
                r["_field"] == "frame" or
                r["_field"] == "user")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> filter(fn: (r) => r[\"processed\"] == false)
            |> sort(columns: ["_time"], desc: false)  
            |> limit(n:{frames}, offset: 0)'''

        # query result as dataframe
        dataframe = self._get_query_api().query_data_frame(query=get_frames_to_process)
        return dataframe


    def save_raw_frame(self, satellite: str, link: str, timestamp: datetime, tlm: dict) -> bool:
        """Write frame to corresponding satellite table (if not already stored).
        Returns True if the frame was stored and False otherwise (if the frame is already stored).
        Also store the frame with processed = False."""

        bucket = satellite + "_raw_data"
        #tlm_time = datetime.strptime(tlm['timestamp'], TIME_FORMAT)
        #logger.info("Timestamp type " + str(type(tlm_time)))

        time_range_lower_bound = (timestamp - timedelta(seconds=1)).strftime(TIME_FORMAT)
        time_range_upper_bound = (timestamp + timedelta(seconds=1)).strftime(TIME_FORMAT)

        # check if frame already exists
        query = f'''from(bucket: "{bucket}")
            |> range(start: {time_range_lower_bound}, stop: {time_range_upper_bound})
            |> filter(fn: (r) => r._measurement == "raw")
            |> filter(fn: (r) => r["_field"] == "frame" and r["_value"] == "{tlm["frame"]}")
            '''
        # store frame only if not stored already
        if len(self._get_query_api().query(query=query)) != 0:
            logger.info("Found!")
            return False

        tlm["processed"] = False
        tlm["invalid"] = False

        tags = {}

        bucket = satellite + "_raw_data"

        db_fields = {
            "measurement": "raw",
            "time": timestamp,
            "tags": {},
            "fields": tlm
        }

        self._get_write_api().write(bucket, self.organization, db_fields)

        return True


    def save_processed_frame(self, bucket: str, measurement: str, timestamp, tags, fields):
        """Write frame to corresponding satellite table (if not already stored).
        Returns True if the frame was stored and False otherwise (if the frame is already stored).
        Also store the frame with processed = False."""

        #bucket = satellite + "_" + link

        #time_range_lower_bound = (timestamp - timedelta(seconds=1)).strftime(TIME_FORMAT)
        #time_range_upper_bound = (timestamp + timedelta(seconds=1)).strftime(TIME_FORMAT)

        # check if frame already exists
        #query = f'''from(bucket: "{bucket}")
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

        tags = {}

        db_fields = {
            "measurement": measurement,
            "time": timestamp,
            "tags": tags,
            "fields": fields
        }

        self._get_write_api().write(bucket, self.organization, db_fields)


    def update_raw_frame(self, satellite: str, link: str, timestamp: datetime, tlm: dict) -> bool:
        """Updates frame in corresponding satellite table (if not already stored).
        Returns True if the frame was updated and False otherwise (if the frame was not found).
        """

        bucket = satellite + "_raw_data"
        #tlm_time = datetime.strptime(tlm['timestamp'], TIME_FORMAT)
        #logger.info("Timestamp type " + str(type(tlm_time)))

        time_range_lower_bound = (timestamp - timedelta(seconds=1)).strftime(TIME_FORMAT)
        time_range_upper_bound = (timestamp + timedelta(seconds=1)).strftime(TIME_FORMAT)

        # check if frame already exists
        query = f'''from(bucket: "{bucket}")
            |> range(start: {time_range_lower_bound}, stop: {time_range_upper_bound})
            |> filter(fn: (r) => r._measurement == "raw")
            '''

        # update frame only if already present
        if len(self._get_query_api().query(query=query)) != 0:
            logger.info("Update found!")
            bucket = satellite + "_raw_data"

            db_fields = {
                "measurement": "raw",
                "time": timestamp,
                "tags": {},
                "fields": tlm
            }

            self._get_write_api().write(bucket, self.organization, db_fields)
            logger.info("Updated " + str(tlm))
            return True

        return False
