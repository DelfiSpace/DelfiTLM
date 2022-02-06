"""Scripts for saving the frames into the database"""
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from skyfield.api import load, EarthSatellite
import pytz
from ewilgs.models import Downlink, TLE, Satellite
from members.models import Member


def register_downlink_frames(frames_to_add, username=None) -> None:
    """Adds a list of json frames to the downlink table

    Args:
        input: a json containing a list of json object, each of them being a frame
        to be added to the downlink table.
    """
    for frame in frames_to_add['frames']:
        add_frame(frame, username)

def add_frame(frame, username=None, application=None) -> None:
    """Adds one json frame to the downlink table"""
    downlink_entry = Downlink()

    # assign values
    if 'frequency' in frame or frame['frequency'] is not None:
        downlink_entry.frequency = frame['frequency']
    downlink_entry.frame = frame['frame']
    if 'qos' in frame or frame['qos'] is not None:
        downlink_entry.qos = frame['qos']

    if username is not None:
        downlink_entry.radio_amateur = Member.objects.get(username=username)

    # if present, store the application name/version used to submit the data
    if application is not None:
        downlink_entry.version = application

    # always mark the frame to be processed
    downlink_entry.processed = False

    if 'frame_time' not in frame or frame['frame_time'] is None:
        downlink_entry.frame_time = timezone.now().astimezone(pytz.utc)
    else:
        downlink_entry.frame_time = parse_datetime(frame['frame_time']).astimezone(pytz.utc)

    if 'send_time' not in frame or frame['send_time'] is None:
        downlink_entry.send_time = timezone.now().astimezone(pytz.utc)
    else:
        downlink_entry.send_time = parse_datetime(frame['send_time']).astimezone(pytz.utc)

    if 'receive_time' not in frame or frame['receive_time'] is None:
        downlink_entry.receive_time = timezone.now().astimezone(pytz.utc)
    else:
        downlink_entry.receive_time = parse_datetime(frame['receive_time']).astimezone(pytz.utc)

    # save entry
    downlink_entry.save()

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
    # tz = pytz.timezone('Europe/Amsterdam')
    # epoch = satellite.epoch.astimezone(tz)
    tle_instance = TLE()
    tle_instance.valid_from = epoch
    tle_instance.sat = Satellite.objects.get(sat=sat)
    tle_instance.tle = tle

    tle_instance.save()

    return tle_instance
