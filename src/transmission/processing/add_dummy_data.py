"""Methods to populate influxdb buckets"""

import json
from transmission.processing import XTCEParser

from transmission.processing.process_raw_bucket import store_frame, store_raw_frame


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
                store_frame(satellite,
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
