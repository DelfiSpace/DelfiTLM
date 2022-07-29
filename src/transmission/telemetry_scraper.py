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

TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

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
    scraped_telemetry[satellite] = {
        "uplink": [],
        "downlink": []
    }

    with open(SCRAPED_TLM_FILE, "w", encoding="utf-8") as file:
        file.write(json.dumps(scraped_telemetry, indent=4))


def include_timestamp_in_scraped_tlm_range(satellite, link, timestamp):
    """This function ensures that a given timestamp will be included in the scraped
    telemetry time range such that it can then be processed and parsed from raw form."""

    tlm_time = datetime.strptime(timestamp, TIME_FORMAT)

    start_time = (tlm_time - timedelta(seconds=1)).strftime(TIME_FORMAT)
    end_time = (tlm_time + timedelta(seconds=1)).strftime(TIME_FORMAT)

    update_scraped_tlm_timestamps(satellite, link, start_time, end_time)


def update_scraped_tlm_timestamps(satellite, link, start_time, end_time) -> None:
    """Bookkeep time range of unprocessed telemetry."""
    scraped_tlm = read_scraped_tlm()

    # No time range saved
    if scraped_tlm[satellite][link] == []:
        scraped_tlm[satellite][link] = [start_time, end_time]
    # Update time range
    else:
        scraped_tlm[satellite][link][0] = min(scraped_tlm[satellite][link][0], start_time)
        scraped_tlm[satellite][link][1] = max(scraped_tlm[satellite][link][1], end_time)

    with open(SCRAPED_TLM_FILE, "w", encoding="utf-8") as file:
        json.dump(scraped_tlm, file, indent=4)


def get_satnogs_headers() -> dict:
    """Get satnogs request headers"""

    with open("src/tokens/satnogs_token.txt", "r", encoding="utf-8") as file:
        cookie_auth = file.read()

    headers = {'accept': 'application/json', 'Authorization': 'Token ' + cookie_auth}
    return headers


def get_satnogs_params(satellite: str) -> dict:
    """Get satnogs request parameters"""

    now = datetime.utcnow().strftime(TIME_FORMAT)
    print("Now: " + now)
    #params = {'app_source':'network', 'end': now, 'format': 'json', 'satellite': '51074'}
    params = {'end': now, 'format': 'json', 'satellite': SATELLITES[satellite]}
    return params


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
    |> filter(fn: (r) => r["_field"] == "frame" and r["_value"] == "{tlm["frame"]}")
    '''
    # store frame only if not stored already
    if len(query_api.query(query=query)) != 0:
        return False

    tlm["processed"] = False
    write_frame_to_raw_bucket(write_api, satellite, link, tlm["timestamp"], tlm)
    return True


def save_raw_frame_to_influxdb(satellite: str, link: str, telemetry) -> bool:
    """Connect to influxdb and process raw telemetry.
    Return True if telemetry was stored, False otherwise."""

    write_api, query_api = get_influx_db_read_and_query_api()

    stored = False

    if isinstance(telemetry, list):
        for tlm in telemetry:
            stored = stored or commit_frame(write_api, query_api, satellite, link, tlm)
    elif isinstance(telemetry, dict):
        stored = stored or commit_frame(write_api, query_api, satellite, link, telemetry)

    return stored

def dump_telemetry_to_file(satellite: str, telemetry: list) -> None:
    """Dump json telemetry to file"""

    with open(satellite + ".json", "w", encoding="utf-8") as file:
        file.write(json.dumps(telemetry, indent=4, sort_keys=True))


def strip_tlm(telemetry: dict, fields: list) -> dict:
    """Retrieve only a selection of fields from the telemetry dict."""
    stripped_tlm = {}
    for field in fields:
        if field in telemetry.keys():
            stripped_tlm[field] = telemetry[field]
    return stripped_tlm

def strip_tlm_list(telemetry: list, fields: list) -> list:
    """Retrieve only a selection of fields from the telemetry dict for a list of tlm dicts."""
    stripped_tlm_list = []
    for tlm in telemetry:
        stripped_tlm_list.append(strip_tlm(tlm, fields))
    return stripped_tlm_list


def scrape(satellite: str, save_to_db=True, save_to_file=False) -> None:
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
            first = telemetry_tmp[0]

            # concatenate telemetry
            telemetry = telemetry + telemetry_tmp

            last_time = datetime.strptime(last['timestamp'], TIME_FORMAT)
            next_time = last_time - timedelta(seconds=1)
            print("Next " + next_time.strftime(TIME_FORMAT))

            if save_to_db:
                fields_to_save = ["frame", "timestamp", "observer"]
                stripped_tlm = strip_tlm_list(telemetry_tmp, fields_to_save)
                stored = save_raw_frame_to_influxdb(satellite, "downlink", stripped_tlm)
                # stop scraping if frames are already stored
                if stored:
                    # print("DB successfully updated.")
                    # break
                    print("Stored frame")
                    update_scraped_tlm_timestamps(satellite, "downlink",
                                                  first["timestamp"], last["timestamp"])

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
