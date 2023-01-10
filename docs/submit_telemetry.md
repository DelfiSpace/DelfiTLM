---
layout: default
title: Telemetry Submissions
nav_order: 4
---

# How to submit telemetry?

To submit telemetry, an account needs to be created and an API key needs to be generated. Afterwards, using the template code below, telemetry frames can be pushed to the server API by plugging in the required input: the frame to be submitted, its reception timestamp and the API key. Given that the input passes the validation checks, the frame will be accepted by the system.

```python
from datetime import datetime
import json
from typing import Union

import requests


def create_packet(frame: str, timestamp: str) -> dict:
    """Embeds a frame and timestamp into a json packet."""

    packet = {'timestamp': timestamp, 'frame': frame.upper(), 'link': "downlink"}

    # print(packet)
    return packet


def send_packet(packet: Union[list, dict], api_key: str) -> None:
    """Submits telemetry to the Delfi Space Telemetry server via HTTP."""
    url = "https://delfispace.tudelft.nl/submit/"

    header = {'AUTHORIZATION': api_key, "User-Agent": "gr-satellite"}
    try:
        response = requests.post(url, data=json.dumps(packet), headers=header, timeout=3)
        if response.status_code != 201:
            print(f"Error {response.status_code}: {response.text}")
        else:
            print("Success")
    except requests.exceptions.RequestException as exception:
        print(exception)


def create_batched_submission(frame_timestamp_tuple_list: list) -> list:
    """Creates a list of json frame packets to batch frames into one submission."""
    packet = []
    for frame, timestamp in frame_timestamp_tuple_list:
        packet.append(create_packet(frame, timestamp))

    return packet


# Test
FRAME = "8EA49EAA9C88E088988C92A0A26103F000081A015002000120F3004E0000000E0A0000641302002CC00C60000B"
TIMESTAMP = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

# Add your key here
API_KEY = ""

# for single frame submissions
PACKET = create_packet(FRAME, TIMESTAMP)
# for batched submissions
PACKET = create_batched_submission([(FRAME, TIMESTAMP)])

send_packet(PACKET, API_KEY)
```
