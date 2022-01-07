"""Scripts for saving the frames into the database"""
import datetime as dt

from members.models import Member
from .models import Downlink

def register_downlink_frames(frames_to_add, username=None) -> None:
    """Adds a list of json frames to the downlink table

    Args:
        input: a json containing a list of json object, each of them being a frame
        to be added to the downlink table.
    """
    for frame in frames_to_add['frames']:
        add_frame(frame, username)

def add_frame(frame, username) -> None:
    """Adds one json frame to the downlink table"""
    downlink_entry = Downlink()

    # assign values
    downlink_entry.frequency = frame['frequency']
    downlink_entry.frame = frame['frame']
    downlink_entry.qos = frame['qos']

    if username is not None:
        downlink_entry.radio_amateur = Member.objects.get(username=username)

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
