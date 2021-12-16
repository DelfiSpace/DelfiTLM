from ewilgs.models import Uplink, Downlink
import json
import datetime as dt


def registerDownlinkFrames(input) -> None:
    """Adds a list of json frames to the downlink table

    Args:
        input: a json containing a list of json object, each of them being a frame to be added to the downlink table.
    """
    frames_to_add = json.loads(input)
    for frame in frames_to_add['frames']:
        dowlink_entry = Downlink()

        # assign values
        dowlink_entry.frequency = frame['frequency']
        dowlink_entry.data = frame['data']

        if 'processed' not in frame or frame['processed'] is None:
            dowlink_entry.processed = False
        else:
            dowlink_entry.processed = frame['processed']

        if frame['receive_at'] is None:
            dowlink_entry.received_at = dt.now()
        else:
            dowlink_entry.received_at = frame['received_at']

        # save entry
        dowlink_entry.save()
