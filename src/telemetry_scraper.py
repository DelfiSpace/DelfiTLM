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


SATELLITES = {
    "delfi_pq": '51074',
    "delfi_next": '39428',
    "delfi_c3": '32789',
    "da_vinci": '51074'
}


def get_satnogs_headers():
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


def commit_frame(write_api, query_api, satellite: str, tlm: dict):
    """Write frame to corresponding satellite table (if not already stored)"""
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

    fields = ["norad_cat_id", "observer", "version", "sat_id", "frame"]

    for field in fields:
        db_fields["fields"][field] = tlm[field]

    time_range_lower_bound = (tlm_time - timedelta(seconds=1)).strftime(time_format)
    time_range_upper_bound = (tlm_time + timedelta(seconds=1)).strftime(time_format)

    # check if frame already exists
    query = f'''from(bucket: "{bucket}")
    |> range(start: {time_range_lower_bound}, stop: {time_range_upper_bound})
    |> filter(fn: (r) => r["_field"] == "frame" and r["_value"] == "{tlm["frame"]}")
    '''
    # # store frame only if not stored already
    if len(query_api.query(query=query)) != 0:
        return

    write_api.write(bucket, INFLUX_ORG, db_fields)


def save_raw_frame_to_influxdb(satellite: str, telemetry) -> None:
    """Connect to influxdb and process raw telemetry"""

    with open("src/tokens/influxdb_token.txt", "r", encoding="utf-8") as file:
        token = file.read()

    client = InfluxDBClient(url="http://localhost:8086", token=token, org=INFLUX_ORG)

    write_api = client.write_api(write_options=SYNCHRONOUS)
    query_api = client.query_api()

    if isinstance(telemetry, list):
        for tlm in telemetry:
            commit_frame(write_api, query_api, satellite, tlm)
    elif isinstance(telemetry, dict):
        commit_frame(write_api, query_api, satellite, telemetry)


def dump_telemetry_to_file(satellite: str, telemetry: list) -> None:
    """Dump json telemetry to file"""

    with open(satellite + ".json", "w", encoding="utf-8") as file:
        file.write(json.dumps(telemetry, indent=4, sort_keys=True))


def scrape(satellite: str, save_to_db=True, save_to_file=True):
    """Scrape satnogs for new telemetry"""

    telemetry = []
    telemetry_tmp = []

    while True:

        response = requests.get(
            PATH,
            params=get_satnogs_params(satellite),
            headers=get_satnogs_headers()
            )
        telemetry_tmp = response.json()
        # print(telemetry_tmp)
        try:
            last = telemetry_tmp[-1]
            last_time = last['timestamp']

            # concatenate telemetry
            telemetry = telemetry + telemetry_tmp

            last_time = datetime.strptime(last['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
            next_time = last_time - timedelta(seconds=1)
            now = next_time.strftime("%Y-%m-%dT%H:%M:%SZ")

            if save_to_db:
                save_raw_frame_to_influxdb(satellite, telemetry_tmp)

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

scrape("delfi_pq")
# scrape("delfi_next")
# scrape("delfi_c3")
