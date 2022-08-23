"""Methods to populate DelfiPQ influxdb buckets"""

import json
from transmission.processing import XTCEParser

from delfipq.process_raw_telemetry import store_frame, store_raw_frame


def delfi_pq_add_dummy_tlm_data():
    """Add dummy processed telemetry intended to test and experiment with dashboards."""
    inputfile = "delfipq/delfi-pq.txt"
    with open(inputfile, encoding="utf-8") as file:
        data = json.load(file)
        # sort messages in chronological order
        data.sort(key=lambda x: x["timestamp"])
        # data = data[:100]
        # process each frame
        for frame in data:
            try:
                store_frame(frame["timestamp"], frame["frame"], frame["observer"], "downlink")
            except XTCEParser.XTCEException as _:
                # ignore
                pass
    return len(data)

def delfi_pq_add_dummy_tlm_raw_data():
    """Add dummy raw telemetry"""
    inputfile = "delfipq/delfi-pq.txt"
    stored_frames = 0
    with open(inputfile, encoding="utf-8") as file:
        data = json.load(file)
        # sort messages in chronological order
        data.sort(key=lambda x: x["timestamp"])
        # data = data[:100]
        # process each frame
        for frame in data:
            stored = store_raw_frame(frame["timestamp"],
                                     frame["frame"],
                                     frame["observer"],
                                     "downlink")
            if stored:
                stored_frames += 1

    return len(data), stored_frames
