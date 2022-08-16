"""Scripts for saving the frames into the database"""
import re
import copy
import json
from django.forms import ValidationError
from django.core.exceptions import BadRequest
from django.utils.dateparse import parse_datetime
from skyfield.api import load, EarthSatellite
import pytz
from transmission.models import Uplink, Downlink, TLE, Satellite
from members.models import Member
import transmission.telemetry_scraper as tlm_scraper


def store_frame(frame, link, username, application=None) -> None:
    """Adds one json frame to the uplink/downlink table"""

    frame_entry = None

    if username is not None:
        user = Member.objects.get(username=username)

        if link == "uplink":
            if not user.has_perm("transmission.add_uplink"):
                raise BadRequest()
            frame_entry = Uplink()
            frame_entry.operator = user

        elif link == "downlink":
            if not user.has_perm("transmission.add_downlink"):
                raise BadRequest()
            frame_entry = Downlink()
            frame_entry.observer = user
        else:
            raise ValueError("Invalid frame link.")

    # if present, store the application name/version used to submit the data
    if application is not None:
        frame_entry.application = application

    check_valid_frame(frame)
    # copy fields from frame to frame_entry
    frame_entry = parse_submitted_frame(frame, frame_entry)

    frame_entry.save()


def check_valid_frame(frame):
    """Check if a given frame has a valid form and a timestamp."""
    # check if the frame exists and it is a HEX string
    non_hex = re.match("^[A-Fa-f0-9]+$", frame["frame"])
    if non_hex is None:
        raise ValidationError("Invalid frame, not an hexadecimal value.")

    # check is a timestamp is attached
    if "timestamp" not in frame or frame["timestamp"] is None:
        raise ValidationError("Invalid submission, no timestamp attached.")


def parse_submitted_frame(frame, frame_entry):
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
    # remove previousely parsed fields
    for field in ["frame", "timestamp", "frequency"]:
        if field in metadata:
            del metadata[field]

    frame_entry.metadata = json.dumps(metadata)

    return frame_entry


def process_uplink_and_downlink():
    """Process all unprocessed uplink and downlink frames,
    i.e. move them to the influxdb raw satellite data bucket."""

    downlink_frames = Downlink.objects.all().filter(processed=False)
    process_frames(downlink_frames, "downlink")

    uplink_frames = Uplink.objects.all().filter(processed=False)
    process_frames(uplink_frames, "uplink")

    return len(downlink_frames), len(uplink_frames)

def process_frames(frames, link) -> int:
    """Try to store frame to influxdb and set the processed flag to True
    if a frame was sucessfully stored in influxdb.
    Returns the count of successfully processed_frames."""

    processed_frames = 0
    for frame_obj in frames:
        frame_dict = frame_obj.to_dictionary()
        stored = store_frame_to_influxdb(frame_dict, link)
        if stored:
            frame_obj.processed = True
            frame_obj.save()
            processed_frames += 1

    return processed_frames

def store_frame_to_influxdb(frame, link) -> bool:
    """Try to store frame to influxdb.
    Returns True if the frame was successfully stored, False otherwise."""

    satellite = get_satellite_from_frame_header(frame["frame"])
    fields_to_save = ["frame", "timestamp", "observer", "frequency", "application", "metadata"]

    frame = tlm_scraper.strip_tlm(frame, fields_to_save)
    stored = tlm_scraper.save_raw_frame_to_influxdb(satellite, link, frame)

    if stored:
        tlm_scraper.include_timestamp_in_scraped_tlm_range(satellite, link, frame["timestamp"])

    return stored


def get_satellite_from_frame_header(frame):
    """Find the corresponding satellite from the frame header"""
    # to be implemented
    print(frame)
    return "delfi_pq"


def save_tle(tle):
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
