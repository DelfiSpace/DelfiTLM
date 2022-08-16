"""Satnogs scraper"""
from datetime import datetime, timedelta
import json
import time
import re
import requests
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

PATH = "https://db.satnogs.org/api/telemetry/"
INFLUX_ORG = "Delfi Space"
SCRAPED_TLM_FILE = "scraped_telemetry.json"

SATELLITES = {
    "delfi_pq": '51074',
    "delfi_next": '39428',
    "delfi_c3": '32789',
    "da_vinci": '51074'  #update id
}

def get_influx_db_read_and_query_api() -> tuple:
    """Connect to influxdb and return write_api and query_api."""
    with open("src/tokens/influxdb_token.txt", "r", encoding="utf-8") as file:
        token = file.read()

    client = InfluxDBClient(url="http://localhost:8086", token=token, org=INFLUX_ORG)

    write_api = client.write_api(write_options=SYNCHRONOUS)
    query_api = client.query_api()

    return (write_api, query_api)


def read_scraped_tlm() -> dict:
    """Read scraped_telemetry.json."""
    scraped_telemetry = {}
    with open(SCRAPED_TLM_FILE, "r", encoding="utf-8") as file:
        scraped_telemetry = json.load(file)

    return scraped_telemetry


def reset_scraped_tlm_timestamps(satellite: str) -> None:
    """Replace timestamps in scraped_telemetry.json with []."""
    scraped_telemetry = read_scraped_tlm()
    scraped_telemetry[satellite] = []

    with open(SCRAPED_TLM_FILE, "w", encoding="utf-8") as file:
        file.write(json.dumps(scraped_telemetry, indent=4))


def update_scraped_tlm_timestamps(satellite, start_time, end_time) -> None:
    """Bookkeep time range of unprocessed telemetry."""
    scraped_telemetry = read_scraped_tlm()
    if scraped_telemetry[satellite] == []:
        scraped_telemetry[satellite] = [start_time, end_time]
    else:
        scraped_telemetry[satellite][0] = min(scraped_telemetry[satellite][0], start_time)
        scraped_telemetry[satellite][1] = max(scraped_telemetry[satellite][1], end_time)

    with open(SCRAPED_TLM_FILE, "w", encoding="utf-8") as file:
        json.dump(scraped_telemetry, file, indent=4)


def get_satnogs_headers() -> dict:
    """Get satnogs request headers"""

    with open("src/tokens/satnogs_token.txt", "r", encoding="utf-8") as file:
        cookie_auth = file.read()

    headers = {'accept': 'application/json', 'Authorization': 'Token ' + cookie_auth}
    return headers


def get_satnogs_params(satellite: str) -> dict:
    """Get satnogs request parameters"""

    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print("Now: " + now)
    #params = {'app_source':'network', 'end': now, 'format': 'json', 'satellite': '51074'}
    params = {'end': now, 'format': 'json', 'satellite': SATELLITES[satellite]}
    return params


def override_raw_frame_processed_flag(write_api, satellite, timestamp, frame, observer) -> None:
    """Mark raw data frame as processed."""
    tags = {}

    db_fields = {
    "measurement": satellite + "_raw_data",
    "time": timestamp,
    "tags": tags,
    "fields": {
        "processed": True,
        "frame": frame,
        "obeserver": observer,
        }
    }

    write_api.write(satellite, INFLUX_ORG, db_fields)


def commit_frame(write_api, query_api, satellite: str, tlm: dict) -> bool:
    """Write frame to corresponding satellite table (if not already stored).
    Returns True if the frame was stored and False otherwise (if the frame is already stored)."""

    bucket = satellite + "_raw_data"
    tags = {}

    time_format = '%Y-%m-%dT%H:%M:%SZ'
    tlm_time = datetime.strptime(tlm['timestamp'], time_format)

    db_fields = {
        "measurement": satellite + "_raw_data",
        "time": tlm["timestamp"],
        "tags": tags,
        "fields": {
            "processed": False,
        }
    }

    fields = ["observer", "frame"]

    for field in fields:
        db_fields["fields"][field] = tlm[field]

    time_range_lower_bound = (tlm_time - timedelta(seconds=1)).strftime(time_format)
    time_range_upper_bound = (tlm_time + timedelta(seconds=1)).strftime(time_format)

    # check if frame already exists
    query = f'''from(bucket: "{bucket}")
    |> range(start: {time_range_lower_bound}, stop: {time_range_upper_bound})
    |> filter(fn: (r) => r["_field"] == "frame" and r["_value"] == "{tlm["frame"]}")
    '''
    # store frame only if not stored already
    if len(query_api.query(query=query)) != 0:
        return False

    write_api.write(bucket, INFLUX_ORG, db_fields)
    return True


def save_raw_frame_to_influxdb(satellite: str, telemetry) -> bool:
    """Connect to influxdb and process raw telemetry.
    Return True if telemetry was stored, False otherwise."""

    write_api, query_api = get_influx_db_read_and_query_api()

    stored = False

    if isinstance(telemetry, list):
        for tlm in telemetry:
            stored = stored or commit_frame(write_api, query_api, satellite, tlm)
    elif isinstance(telemetry, dict):
        stored = stored or commit_frame(write_api, query_api, satellite, telemetry)

    return stored

def dump_telemetry_to_file(satellite: str, telemetry: list) -> None:
    """Dump json telemetry to file"""

    with open(satellite + ".json", "w", encoding="utf-8") as file:
        file.write(json.dumps(telemetry, indent=4, sort_keys=True))


def scrape(satellite: str, save_to_db=True, save_to_file=True) -> None:
    """Scrape satnogs for new telemetry"""

    telemetry = []
    telemetry_tmp = []

    while True:
        satnogs_params = get_satnogs_params(satellite)
        response = requests.get(
            PATH,
            params=satnogs_params,
            headers=get_satnogs_headers()
        )
        telemetry_tmp = response.json()
        # print(telemetry_tmp)
        try:
            last = telemetry_tmp[-1]
            last_time = last['timestamp']
            first = telemetry_tmp[0]

            # concatenate telemetry
            telemetry = telemetry + telemetry_tmp

            last_time = datetime.strptime(last['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
            next_time = last_time - timedelta(seconds=1)
            now = next_time.strftime("%Y-%m-%dT%H:%M:%SZ")

            if save_to_db:
                stored = save_raw_frame_to_influxdb(satellite, telemetry_tmp)
                # stop scraping if frames are already stored
                if stored:
                    # print("DB successfully updated.")
                    # break
                    print("Stored frame")
                    update_scraped_tlm_timestamps(satellite, first["timestamp"], last["timestamp"])

            print("Next " + now)

        except IndexError:
            break

        except KeyError:
            print(telemetry_tmp)
            if 'detail' in telemetry_tmp:
                if "throttled" in telemetry_tmp["detail"]:
                    delay = re.findall('[0-9]+', telemetry_tmp["detail"])[0]
                    print("Sleeping " + str(delay) + " s (request throttled)")
                    time.sleep(int(delay))
                else:
                    break
            else:
                break

        if save_to_file:
            dump_telemetry_to_file(satellite, telemetry)
