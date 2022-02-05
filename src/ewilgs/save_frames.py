"""Scripts for saving the frames into the database"""
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from members.models import Member
from .models import Downlink
import re

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

    # check if the frame exists and it is a HEX string
    nonHex = re.match("[^0-9A-Fa-f]", frame['frame'])
    if nonHex:
        raise ValueError("Invalid frame, not an hexadecimal value.")

    # assign the frame HEX values
    downlink_entry.frame = frame['frame']

    # assign the timestamp
    downlink_entry.receive_time = parse_datetime(frame['timestamp'])

    # assign frequency, if present
    if 'frequency' in frame or frame['frequency'] is not None:
        downlink_entry.frequency = frame['frequency']

    # assign qos, if present
    if 'qos' in frame or frame['qos'] is not None:
        downlink_entry.qos = frame['qos']

    if username is not None:
        downlink_entry.radio_amateur = Member.objects.get(username=username)

    # if present, store the application name/version used to submit the data
    if application is not None:
        downlink_entry.version = application

    # always mark the frame to be processed
    downlink_entry.processed = False

    # save entry
    downlink_entry.save()

