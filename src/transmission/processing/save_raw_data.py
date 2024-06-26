"""Scripts for saving the frames into the database"""
import os
import re
import copy
import json
from typing import Union

from django.forms import ValidationError
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models.query import QuerySet
from django.utils.dateparse import parse_datetime
from skyfield.api import load, EarthSatellite
import pytz
from django_logger import logger
from members.models import Member
from transmission.models import Uplink, Downlink, TLE, Satellite
from transmission.processing.XTCEParser import SatParsers, XTCEException
from transmission.processing.bookkeep_new_data_time_range import get_new_data_buffer_temp_folder, \
    include_timestamp_in_time_range, save_timestamps_to_file
from transmission.processing.influxdb_api import save_raw_frame_to_influxdb
from transmission.processing.telemetry_scraper import strip_tlm


def store_frames(frames, username: str, application: str = None) -> int:
    """Store frames in batches if the input is a list.
    Otherwise, in case of a dict, the frame is parsed and stored."""
    if isinstance(frames, dict):
        frame_object = build_frame_model_object(frames, username, application)
        frame_object.save()
        return 1

    if isinstance(frames, list):
        frame_objects_uplink = []
        frame_objects_downlink = []

        for frame in frames:
            frame_object = build_frame_model_object(frame, username, application)
            if isinstance(frame_object, Uplink):
                frame_objects_uplink.append(frame_object)
            elif isinstance(frame_object, Downlink):
                frame_objects_downlink.append(frame_object)

        # batch uplink/downlink frames into 1 database commit
        Uplink.objects.bulk_create(frame_objects_uplink)
        Downlink.objects.bulk_create(frame_objects_downlink)

        return len(frame_objects_downlink) + len(frame_objects_uplink)

    raise ValidationError("Invalid frame, not JSON object or array.")


def build_frame_model_object(frame: dict, username: str, application: str = None) -> models.Model:
    """Adds one json frame to the uplink/downlink table"""

    frame_entry = None

    if "link" not in frame:
        frame["link"] = "downlink"

    user = Member.objects.get(username=username)

    if frame["link"] == "uplink":
        if not user.has_perm("transmission.add_uplink"):
            raise PermissionDenied()
        frame_entry = Uplink()
        frame_entry.operator = user

    elif frame["link"] == "downlink":
        if not user.has_perm("transmission.add_downlink"):
            raise PermissionDenied()
        frame_entry = Downlink()
        frame_entry.observer = user.UUID

    else:
        raise ValidationError("Invalid frame link.")

    # store the application name/version used to submit the data (can be null)
    frame_entry.application = application

    check_valid_frame(frame)
    # copy fields from frame to frame_entry
    frame_entry = parse_submitted_frame(frame, frame_entry)

    return frame_entry


def check_valid_frame(frame: dict) -> None:
    """Check if a given frame has a valid form and a timestamp."""
    # check if the frame exists, and it is a HEX string
    non_hex = re.match("^[A-Fa-f0-9]+$", frame["frame"])
    if non_hex is None:
        raise ValidationError("Invalid frame, not an hexadecimal value.")

    # check is a timestamp is attached
    if "timestamp" not in frame or frame["timestamp"] is None:
        raise ValidationError("Invalid submission, no timestamp attached.")


def parse_submitted_frame(frame: dict, frame_entry: models.Model) -> models.Model:
    """Extract frame info from frame and store it into frame_entry (database frame)"""
    # assign the frame HEX values
    frame_entry.frame = frame['frame']
    # assign the timestamp
    frame_entry.timestamp = parse_datetime(frame["timestamp"]).astimezone(pytz.utc)
    # assign frequency, if present
    if "frequency" in frame and frame["frequency"] is not None:
        frame_entry.frequency = frame["frequency"]

    # add metadata
    metadata = copy.deepcopy(frame)
    # remove previously parsed fields
    for field in ["frame", "timestamp", "frequency"]:
        if field in metadata:
            del metadata[field]

    frame_entry.metadata = json.dumps(metadata)

    return frame_entry


def process_uplink_and_downlink() -> tuple:
    """Process all unprocessed uplink and downlink frames,
    i.e. move them to the influxdb raw satellite data bucket."""

    downlink_frames = Downlink.objects.all().filter(processed=False)
    process_frames(downlink_frames, "downlink")

    uplink_frames = Uplink.objects.all().filter(processed=False)
    process_frames(uplink_frames, "uplink")

    return len(downlink_frames), len(uplink_frames)


def process_frames(frames: QuerySet, link: str) -> int:
    """Try to store frame to influxdb and set the processed flag to True
    if a frame was successfully stored in influxdb.
    Returns the count of successfully processed_frames."""

    processed_frames = 0
    processed_frames_timestamps = {}
    for frame_obj in frames:
        frame_dict = frame_obj.to_dictionary()
        stored, satellite = store_frame_to_influxdb(frame_dict, link)
        if stored:
            frame_obj.processed = True
            frame_obj.invalid = False
            frame_obj.save()
            processed_frames += 1
            if satellite not in processed_frames_timestamps:
                processed_frames_timestamps[satellite] = include_timestamp_in_time_range(
                    satellite, link,
                    frame_obj.timestamp,
                    existing_range={}
                )
            else:
                processed_frames_timestamps[satellite] = include_timestamp_in_time_range(
                    satellite, link,
                    frame_obj.timestamp,
                    existing_range=processed_frames_timestamps[satellite]
                )
    for satellite, time_range in processed_frames_timestamps.items():
        path = get_new_data_buffer_temp_folder(satellite)
        path += satellite + "_" + link + "_" + str(len(os.listdir(path))) + ".json"
        save_timestamps_to_file(time_range, path)

    return processed_frames


def mark_frame_as_invalid(frame: str, link: str) -> None:
    """Flag an invalid frame that doesn't correspond to any satellite."""
    if link == "downlink":
        Downlink.objects.filter(frame=frame).update(invalid=True)
    elif link == "uplink":
        Uplink.objects.filter(frame=frame).update(invalid=True)


def store_frame_to_influxdb(frame: dict, link: str) -> tuple:
    """Try to store frame to influxdb.
    Returns True if the frame was successfully stored, False otherwise."""

    satellite = get_satellite_from_frame(frame["frame"])

    if satellite is None:
        mark_frame_as_invalid(frame["frame"], link)
        logger.warning("invalid %s frame, cannot match satellite: %s", link, frame["frame"])
        return False, satellite

    fields_to_save = ["frame", "timestamp", "observer", "frequency", "application", "metadata"]

    frame = strip_tlm(frame, fields_to_save)
    stored = save_raw_frame_to_influxdb(satellite, link, frame)

    return stored, satellite


def get_satellite_from_frame(frame: str) -> Union[str, None]:
    """Find the corresponding satellite by attempting to parse the frame.
    If the parsing is successful, return the satellite name, else None."""
    for sat, parser in SatParsers().parsers.items():
        if parser is not None:
            try:
                parser.processTMFrame(bytes.fromhex(frame))
                return sat
            except XTCEException:
                pass

    return None


def save_tle(tle: str) -> models.Model:
    """Insert a TLE into the database.
        TLE format:
        ISS (ZARYA)
        1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
        2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537
    """
    time_scale = load.timescale()
    tle_split_lines = tle.splitlines()
    sat = tle_split_lines[0]
    line1 = tle_split_lines[1]
    line2 = tle_split_lines[2]

    satellite = EarthSatellite(line1, line2, sat, time_scale)

    epoch = satellite.epoch.utc_datetime()
    # tz = pytz.timezone("Europe/Amsterdam")
    # epoch = satellite.epoch.astimezone(tz)
    tle_instance = TLE()
    tle_instance.valid_from = epoch
    tle_instance.sat = Satellite.objects.get(sat=sat)
    tle_instance.tle = tle

    tle_instance.save()

    return tle_instance
