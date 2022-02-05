"""Scripts for saving frames and TLEs into the database"""
import datetime as dt
from .models import Downlink, TLE
from skyfield.api import load, EarthSatellite

def register_downlink_frames(frames_to_add) -> None:
    """Adds a list of json frames to the downlink table

    Args:
        input: a json containing a list of json object, each of them being a frame
        to be added to the downlink table.
    """
    for frame in frames_to_add['frames']:
        downlink_entry = Downlink()

        # assign values
        downlink_entry.frequency = frame['frequency']
        downlink_entry.frame = frame['frame']
        downlink_entry.qos = frame['qos']

        if 'username' in frame and frame['username'] is not None:
            downlink_entry.radio_amateur = frame['username']

        if 'processed' not in frame or frame['processed'] is None:
            downlink_entry.processed = False
        else:
            downlink_entry.processed = frame['processed']

        if 'frame_time' not in frame or frame['frame_time'] is None:
            downlink_entry.received_at = dt.datetime.utcnow()
        else:
            time_format = '%Y-%m-%dT%H:%M:%S.%fZ'
            downlink_entry.received_at = dt.datetime.strptime(frame['frame_time'], time_format)

        if 'send_time' not in frame or frame['send_time'] is None:
            downlink_entry.received_at = dt.datetime.utcnow()
        else:
            time_format = '%Y-%m-%dT%H:%M:%S.%fZ'
            downlink_entry.received_at = dt.datetime.strptime(frame['send_time'], time_format)

        if 'receive_time' not in frame or frame['receive_time'] is None:
            downlink_entry.received_at = dt.datetime.utcnow()
        else:
            time_format = '%Y-%m-%dT%H:%M:%S.%fZ'
            downlink_entry.received_at = dt.datetime.strptime(frame['receive_time'], time_format)

        # save entry
        downlink_entry.save()


def save_tle(tle):
    """Insert a TLE into the database.
        TLE format:
        ISS (ZARYA)
        1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
        2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537
    """
    ts = load.timescale()
    tle_split_lines = tle.splitlines()
    sat = tle_split_lines[0]
    line1 = tle_split_lines[1]
    line2 = tle_split_lines[2]

    satellite = EarthSatellite(line1, line2, sat, ts)

    epoch = satellite.epoch.utc_jpl()

    tle_instance = TLE()
    tle_instance.valid_from = epoch
    tle_instance.sat = sat
    tle_instance.tle = tle

    tle_instance.save()

    return tle_instance
