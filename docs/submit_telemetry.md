---
layout: default
title: Submit TLM
nav_order: 4
---

# How to submit telemetry?

To submit telemetry, an account needs to be created and an API key needs to be generated. Afterwards, using the template code below, telemetry frames can be pushed to the server API by plugging in the required input: the frame to be submitted, its reception timestamp and the API key. Given that the input passes the validation checks, the frame will be accepted by the system.

```python
from datetime import datetime
import json
import requests

def push_frame(frame: str, timestamp: datetime, api_key: str) -> None:
    """Submits telemetry to the Delfi Space Telemetry server."""

    url = "https://delfispace.tudelft.nl/submit/"

    packet = {}
    packet['timestamp'] = timestamp
    packet['frame'] = frame.upper()
    packet['link'] = "downlink" # optional, defaults to downlink

    # print(packet)

    header = {'AUTHORIZATION': api_key, "User-Agent": "gr-satellite"}
    try:
        response = requests.post(url, data=json.dumps(packet), headers=header, timeout=3)
        if response.status_code != 201:
            print(f"Error {response.status_code}: {response.text}")
        else:
            print("Success")
    except requests.exceptions.RequestException as exception:
        print(exception)

# Test
FRAME = ""
TIMESTAMP = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
# Add your key here
API_KEY = ""

push_frame(FRAME, TIMESTAMP, API_KEY)
```
