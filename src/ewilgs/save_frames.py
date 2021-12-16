"""Scripts for saving the frames into the database"""
import datetime as dt
from .models import Downlink

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

        if 'processed' not in frame or frame['processed'] is None:
            downlink_entry.processed = False
        else:
            downlink_entry.processed = frame['processed']

        if 'frame_time' not in frame or frame['frame_time'] is None:
            downlink_entry.received_at = dt.time()
        else:
            downlink_entry.received_at = frame['frame_time']

        if 'send_time' not in frame or frame['send_time'] is None:
            downlink_entry.received_at = dt.time()
        else:
            downlink_entry.received_at = frame['send_time']

        if 'receive_time' not in frame or frame['receive_time'] is None:
            downlink_entry.received_at = dt.time()
        else:
            downlink_entry.received_at = frame['receive_time']

        # save entry
        downlink_entry.save()
