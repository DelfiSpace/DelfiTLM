"""Satnogs scraper"""
from datetime import datetime, timedelta
import json
import os
import time
import re
import requests

from django_logger import logger
from transmission.processing.satellites import SATELLITES, TIME_FORMAT
from transmission.processing.bookkeep_new_data_time_range import get_new_data_file_path, get_new_data_scraper_temp_folder, \
    include_timestamp_in_time_range, save_timestamps_to_file
from transmission.processing.influxdb_api import save_raw_frame_to_influxdb

SATNOGS_PATH = "https://db.satnogs.org/api/telemetry/"
SATNOGS_TOKEN_PATH = "tokens/satnogs_token.txt"


def get_satnogs_headers() -> dict:
    """Get satnogs request headers"""

    with open(SATNOGS_TOKEN_PATH, "r", encoding="utf-8") as file:
        cookie_auth = file.read()

    headers = {'accept': 'application/json', 'Authorization': 'Token ' + cookie_auth}
    return headers


def get_satnogs_params(satellite: str) -> dict:
    """Get satnogs request parameters"""

    now = datetime.utcnow().strftime(TIME_FORMAT)
    logger.debug("Now: %s", now)
    #params = {'app_source':'network', 'end': now, 'format': 'json', 'satellite': '51074'}
    params = {'end': now, 'format': 'json', 'satellite': SATELLITES[satellite]}
    return params


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
    logger.info("SatNOGS scraper started. Scraping %s telemetry.", satellite)
    time_range = {}
    while True:
        response = requests.get(
            SATNOGS_PATH,
            params=get_satnogs_params(satellite),
            headers=get_satnogs_headers()
        )
        telemetry_tmp = response.json()
        try:
            last = telemetry_tmp[-1]
            first = telemetry_tmp[0]

            # concatenate telemetry
            telemetry = telemetry + telemetry_tmp

            last_time = datetime.strptime(last['timestamp'], TIME_FORMAT)
            next_time = last_time - timedelta(seconds=1)
            logger.debug("Next: %s", next_time.strftime(TIME_FORMAT))

            if save_to_db:
                fields_to_save = ["frame", "timestamp", "observer"]
                stripped_tlm = strip_tlm_list(telemetry_tmp, fields_to_save)
                stored = save_raw_frame_to_influxdb(satellite, "downlink", stripped_tlm)
                if stored:
                    time_range = include_timestamp_in_time_range(
                                satellite, 'downlink', first["timestamp"], existing_range=time_range)
                    time_range = include_timestamp_in_time_range(
                                satellite, 'downlink', last["timestamp"], existing_range=time_range)

                # if the frame is not stored (due to it being stored in a past scrape) and
                # the next request retrieves data older than a week -> stop
                elif (datetime.now() - next_time).days > 7:
                    logger.info("SatNOGS scraper stopped. Done scraping %s telemetry.", satellite)
                    break # stop scraping

        except IndexError:
            logger.info("SatNOGS scraper stopped. Done scraping %s telemetry.", satellite)
            break

        except KeyError:
            logger.debug(telemetry_tmp)
            if 'detail' in telemetry_tmp:
                if "throttled" in telemetry_tmp["detail"]:
                    delay = re.findall('[0-9]+', telemetry_tmp["detail"])[0]
                    logger.debug("Sleeping %s s (request throttled)", delay)
                    time.sleep(int(delay))
                    path = get_new_data_scraper_temp_folder(satellite)
                    path += satellite + "_downlink_" + str(len(os.listdir(path))) + ".json"
                    save_timestamps_to_file(time_range, path)
                else:
                    break
            else:
                break

        if save_to_file:
            dump_telemetry_to_file(satellite, telemetry)
