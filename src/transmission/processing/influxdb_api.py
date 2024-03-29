"""Methods for saving raw data frames and retrieving the influxdb API."""
from datetime import datetime, timedelta
import os
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import traceback

from transmission.processing.satellites import TIME_FORMAT
from django_logger import logger

INFLUXDB_URL = "http://influxdb:8086"
INFLUX_ORG = os.environ.get('INFLUXDB_V2_ORG', 'DelfiSpace')


def get_influxdb_client():
    """Connect to influxdb and return the influxdb client."""

    client = InfluxDBClient(url=INFLUXDB_URL, token=os.environ.get('INFLUXDB_V2_TOKEN', 'adminpwd'), org=INFLUX_ORG)

    return client


def get_influxdb_bucket_api():
    """Connect to influxdb and return bucket_api."""

    client = get_influxdb_client()

    buckets_api = client.buckets_api()

    return buckets_api


def get_influx_db_read_and_query_api() -> tuple:
    """Connect to influxdb and return write_api and query_api."""

    client = get_influxdb_client()

    write_api = client.write_api(write_options=SYNCHRONOUS)
    query_api = client.query_api()

    return (write_api, query_api)


def write_frame_to_raw_bucket(write_api, satellite, link, timestamp, frame_fields) -> None:
    """Save frame given its fields. Note: to update/overwrite a field write the frame again
    with the changed fields and the same timestamp as before."""

    tags = {}

    bucket = satellite + "_raw_data"

    db_fields = {
        "measurement": satellite + "_" + link + "_raw_data",
        "time": timestamp,
        "tags": tags,
        "fields": frame_fields
    }

    #logger.info("%s: raw frame stored or updated. Frame timestamp: %s, link: %s, bucket: %s",
    #            satellite, timestamp, link, bucket)

    write_api.write(bucket, INFLUX_ORG, db_fields)


def commit_frame(write_api, query_api, satellite: str, link: str, tlm: dict) -> bool:
    """Write frame to corresponding satellite table (if not already stored).
    Returns True if the frame was stored and False otherwise (if the frame is already stored).
    Also store the frame with processed = False."""

    bucket = satellite + "_raw_data"
    tlm_time = datetime.strptime(tlm['timestamp'], TIME_FORMAT)

    time_range_lower_bound = (tlm_time - timedelta(seconds=1)).strftime(TIME_FORMAT)
    time_range_upper_bound = (tlm_time + timedelta(seconds=1)).strftime(TIME_FORMAT)

    # check if frame already exists
    query = f'''from(bucket: "{bucket}")
    |> range(start: {time_range_lower_bound}, stop: {time_range_upper_bound})
    |> filter(fn: (r) => r._measurement == "{satellite + "_" + link + "_raw_data"}")
    |> filter(fn: (r) => r["_field"] == "frame" and r["_value"] == "{tlm["frame"]}")
    '''
    # store frame only if not stored already
    if len(query_api.query(query=query)) != 0:
        return False

    tlm["processed"] = False
    write_frame_to_raw_bucket(write_api, satellite, link, tlm["timestamp"], tlm)
    return True

def save_raw_frame_to_influxdb(satellite: str, link: str, telemetry) -> bool:
    """Connect to influxdb and save raw telemetry.
    Return True if telemetry was stored, False otherwise."""

    write_api, query_api = get_influx_db_read_and_query_api()

    stored = False

    if isinstance(telemetry, list):
        for tlm in telemetry:
            stored = stored or commit_frame(write_api, query_api, satellite, link, tlm)
    elif isinstance(telemetry, dict):
        stored = stored or commit_frame(write_api, query_api, satellite, link, telemetry)

    return stored

def get_last_received_frame(satellite: str):
    [write_api, query_api] = get_influx_db_read_and_query_api()
    bucket = satellite + "_raw_data"

    query = f'''from(bucket: "{bucket}")
    |> range(start: -15y)
    |> filter(fn: (r) => r["_measurement"] == "{satellite + "_downlink_raw_data"}")
    |> filter(fn: (r) => r["_field"] == "timestamp")
    |> tail(n: 1)
    '''
    
    try:
       ret = query_api.query(query=query)

       for table in ret:
           return datetime.strptime(table.records[0]["_value"], '%Y-%m-%dT%H:%M:%SZ')

    except:
        e = traceback.format_exc()
        logger.error(e)
