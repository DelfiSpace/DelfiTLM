"""Methods to populate influxdb buckets"""

import json
from django.core.management import call_command

from members.models import Member
from transmission.models import Downlink
from transmission.processing import XTCEParser
from transmission.processing.process_raw_bucket import parse_and_store_frame, store_raw_frame
from transmission.processing.save_raw_data import parse_submitted_frame


def add_dummy_downlink_frames(input_file="transmission/dummy_downlink.json"):
    """Add dummy frames to Downlink table as admin user."""

    # check if admin exists, if not create it
    if len(Member.objects.filter(username="admin")) == 0:
        call_command('initadmin')

    with open(input_file, 'r', encoding="utf-8") as file:
        dummy_data = json.load(file)
        for frame in dummy_data["frames"]:
            frame_entry = Downlink()
            frame_entry.observer = Member.objects.all().filter(username="admin")[0]
            frame_entry = parse_submitted_frame(frame, frame_entry)
            frame_entry.save()


def add_dummy_tlm_data(satellite, input_file):
    """Add dummy processed telemetry intended to test and experiment with dashboards."""
    with open(input_file, encoding="utf-8") as file:
        data = json.load(file)
        # sort messages in chronological order
        data.sort(key=lambda x: x["timestamp"])
        # data = data[:100]
        # process each frame
        for frame in data:
            try:
                parse_and_store_frame(satellite,
                                      frame["timestamp"],
                                      frame["frame"],
                                      frame["observer"],
                                      "downlink"
                                      )
            except XTCEParser.XTCEException as _:
                # ignore
                pass
    return len(data)


def add_dummy_tlm_raw_data(satellite, input_file):
    """Add dummy raw telemetry"""
    stored_frames = 0
    with open(input_file, encoding="utf-8") as file:
        data = json.load(file)
        # sort messages in chronological order
        data.sort(key=lambda x: x["timestamp"])
        # data = data[:100]
        # process each frame
        for frame in data:
            stored = store_raw_frame(satellite,
                                     frame["timestamp"],
                                     frame["frame"],
                                     frame["observer"],
                                     "downlink")
            if stored:
                stored_frames += 1

    return len(data), stored_frames
