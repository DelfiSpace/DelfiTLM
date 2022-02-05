"""Scripts for saving the frames into the database"""
from django.utils.dateparse import parse_datetime
from django.utils import timezone
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
        downlink_entry.frame_time = timezone.now()
    else:
        time_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        downlink_entry.frame_time = parse_datetime(frame['frame_time'])

    if 'send_time' not in frame or frame['send_time'] is None:
        downlink_entry.send_time = timezone.now()
    else:
        downlink_entry.send_time = parse_datetime(frame['send_time'])

    if 'receive_time' not in frame or frame['receive_time'] is None:
        downlink_entry.receive_time = timezone.now()
    else:
        downlink_entry.receive_time = parse_datetime(frame['receive_time'])

    # save entry
    downlink_entry.save()
