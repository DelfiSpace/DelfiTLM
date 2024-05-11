"""Scripts for saving the frames into the database"""
import re
import copy
import json
from typing import Union
import time
from datetime import datetime, timezone
from django.forms import ValidationError
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models.query import QuerySet
from django.utils.dateparse import parse_datetime
from skyfield.api import load, EarthSatellite
from members.models import Member
from transmission.models import Uplink, Downlink, TLE, Satellite
from transmission.processing.XTCEParser import SatParsers, XTCEException
from transmission.processing.influxdb_api import influxdb_api

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
        if "username" not in frame:
            frame_entry.operator = user
        else:
            if user.is_staff:
                frame_entry.operator = frame["username"]
            else:
                raise PermissionDenied()

    elif frame["link"] == "downlink":
        if not user.has_perm("transmission.add_downlink"):
            raise PermissionDenied()
        frame_entry = Downlink()
        if "username" not in frame:
            frame_entry.observer = user
        else:
            if user.is_staff:
                frame_entry.observer = frame["username"]
            else:
                raise PermissionDenied()

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
    frame_entry.timestamp = parse_datetime(frame["timestamp"]).astimezone(timezone.utc)
    # assign frequency, if present
    if "frequency" in frame and frame["frequency"] is not None:
        frame_entry.frequency = frame["frequency"]

    # add metadata
    metadata = copy.deepcopy(frame)
    # remove previously parsed fields
    for field in ["frame", "timestamp", "frequency", "link", "username"]:
        if field in metadata:
            del metadata[field]

    frame_entry.metadata = json.dumps(metadata)

    return frame_entry


def process_uplink_and_downlink(invalid_frames: bool = False, callback = None):
    """Process all processed uplink and downlink frames,
    i.e. move them to the influxdb raw satellite data bucket.
    if invalid_frames is false, only new frames are processed. If 
    invalid_frames is true, only frames already marked as invalid 
    will be processed."""

    iterations = 0

    parsers = SatParsers()
    db = influxdb_api()

    # list the satellites whose frames have been processed:
    # ths allows to later start their processing task
    satellites_list = []

    # once the last frame has been processed, maintain the task active for
    # at least 10 seconds while looking for more frames to process
    while iterations < 50:
        total_processed_frames = 0

        if not invalid_frames:
            # set a maximum length to the results to ensure responsive data processing
            downlink_frames = Downlink.objects.all().filter(processed=False).order_by("timestamp")[:100]
            uplink_frames = Uplink.objects.all().filter(processed=False).order_by("timestamp")[:100]
        else:
            # set a maximum length to the results to ensure responsive data processing
            downlink_frames = Downlink.objects.all().filter(processed=True).filter(invalid=True).order_by("timestamp")[:100]
            uplink_frames = Uplink.objects.all().filter(processed=True).filter(invalid=True).order_by("timestamp")[:100]

        downlink_frames_count = process_frames(parsers, db, downlink_frames, "downlink", satellites_list)
        uplink_frames_count = process_frames(parsers, db, uplink_frames, "uplink", satellites_list)
        total_processed_frames = downlink_frames_count + uplink_frames_count

        # if the satellites list is not empty and the scheduler callback is not None
        if satellites_list and callback is not None:
            # report the satellites that have been sending frames
            callback(satellites_list)
            # empty the list
            satellites_list = []

        # one more iteration
        iterations += 1

        if total_processed_frames != 0:
            # frames were processed in this iteration, reset the iteration counter
            iterations = 0

        # maintain the thread alive and re-check if new frames have been received
        time.sleep(0.2)


def process_frames(parsers: SatParsers, db: influxdb_api, frames: QuerySet, link: str, satellites_list: list) -> int:
    """Try to store frame to influxdb and set the processed flag to True
    if a frame was successfully stored in influxdb.
    Returns the count of successfully processed_frames."""

    processed_frames = 0

    for frame_obj in frames:
        frame_dict = frame_obj.to_dictionary()
        stored, satellite = store_frame_to_influxdb(parsers, db, frame_obj.timestamp, frame_dict, link)
        frame_obj.processed = True

        if stored:
            # valid frame
            frame_obj.invalid = False
            processed_frames += 1

            # satellite found, add it to the processing list
            if satellite not in satellites_list:
                satellites_list.append(satellite)
        else:
            frame_obj.invalid = True

        frame_obj.save()

    return processed_frames


def store_frame_to_influxdb(parsers: SatParsers, db: influxdb_api, timestamp: datetime, frame: dict, link: str) -> tuple:
    """Try to store frame to influxdb.
    Returns True if the frame was successfully stored, False otherwise."""

    satellite = get_satellite_from_frame(parsers, frame["frame"])

    if satellite is None:
        return False, satellite

    stored = db.save_raw_frame(satellite, link, timestamp, frame)

    return stored, satellite


def get_satellite_from_frame(parsers: SatParsers, frame: str) -> Union[str, None]:
    """Find the corresponding satellite by attempting to parse the frame.
    If the parsing is successful, return the satellite name, else None."""
    for sat, parser in parsers.parsers.items():
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
