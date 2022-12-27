"""Frame submitter example"""
from datetime import datetime
import json
import requests


def push_frame(frame: str, timestamp: str, api_key: str) -> None:
    """Submits telemetry to the Delfi Space Telemetry server."""

    url = "http://localhost:8000/submit/"

    packet = {}
    packet['timestamp'] = timestamp
    packet['frame'] = frame.upper()
    packet['link'] = "downlink"  # optional, defaults to downlink

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
FRAME = "8EA49EAA9C88E088988C92A0A26103F000081A015002000120F3004E0000000E0A0000641302002CC00C60000B"
TIMESTAMP = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
# Add your key here
API_KEY = ""

push_frame(FRAME, TIMESTAMP, API_KEY)
