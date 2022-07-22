"""Script to store Delfi-PQ telemetry frames"""
# pylint: disable=E0401
import json
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from XTCEParser import XTCEParser, XTCEException

# pylint: disable = W0621

INPUT_FILE = 'src/delfipq/delfi-pq.txt'
OUTPUT_FILE = 'src/delfipq/EPS_telemetry.csv'

framesList = []

# list of telemetry fields to process
telemetryFields = ["TotalUptime",
                   "BootCounter",
                   "BatteryGGStatus",
                   "BatteryINAStatus",
                   "InternalINAStatus",
                   "UnregulatedINAStatus",
                   "Bus1INAStatus",
                   "Bus2INAStatus",
                   "Bus3INAStatus",
                   "Bus4INAStatus",
                   "PanelYpINAStatus",
                   "PanelYpTMPStatus",
                   "PanelYmINAStatus",
                   "PanelYmTMPStatus",
                   "PanelXpINAStatus",
                   "PanelXpTMPStatus",
                   "PanelXmINAStatus",
                   "PanelXmTMPStatus",
                   "InternalINACurrent",
                   "InternalINAVoltage",
                   "UnregulatedINACurrent",
                   "UnregulatedINAVoltage",
                   "BatteryINAVoltage",
                   "BatteryINACurrent",
                   "BatteryGGTemperature",
                   "BatteryTMP20Temperature",
                   "Bus4Current",
                   "Bus4Voltage",
                   "Bus3Current",
                   "Bus3Voltage",
                   "Bus2Current",
                   "Bus2Voltage",
                   "Bus1Current",
                   "Bus1Voltage",
                   "PanelYpCurrent",
                   "PanelYpVoltage",
                   "PanelYmCurrent",
                   "PanelYmVoltage",
                   "PanelXpCurrent",
                   "PanelXpVoltage",
                   "PanelXmCurrent",
                   "PanelXmVoltage",
                   "PanelYpTemperature",
                   "PanelYmTemperature",
                   "PanelXpTemperature",
                   "PanelXmTemperature",
                   "MCUTemp"]


BUCKET = "delfi_pq"
ORG = "Delfi Space"
with open("src/tokens/influxdb_token.txt", "r", encoding="utf-8") as file:
    token = file.read()

client = InfluxDBClient(url="http://localhost:8086", token=token, org=ORG)

write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

def store_frame(parser, frame):
    """Store frame in influxdb"""

    tags = {
        # "norad_cat_id": frame["norad_cat_id"],
        # "observer": frame["observer"],
        # "sat_id": frame["sat_id"],
        # "version": frame["version"]
    }

    db_fields ={
        "measurement": "delfi_pq_eps",
        "time": frame["timestamp"],
        "tags": tags,
        "fields": {}
        }

    if frame["frame"] not in framesList:
        framesList.append(frame["frame"])
        telemetry = parser.processTMFrame(bytes.fromhex(frame["frame"]))

        if "frame" in telemetry:
            # there is a frame key
            # process only EPS telemetry frames
            # filter by observer
            #  and frame["observer"] == "JA0CAW-PM97nw"
            if telemetry["frame"] == "RadioEPSTelemetry":
                # add the timestamp and the ground station that received the message
                # add each field
                for field in telemetryFields:
                    value = telemetry[field]
                    # try to convert to float
                    try:
                        value = float(value)
                        # if value > 15 and field == "MCUTemp":
                        #     db_fields["tags"]["tag"] = "Err"

                    except ValueError:
                        pass
                    db_fields["fields"][field] = value

                    write_api.write(BUCKET, ORG, db_fields)
                    print(db_fields)
                    db_fields["fields"] = {}
                # query = "select * from delfi_pq"
                # print(query_api.query(query))

parser = XTCEParser("src/delfipq/Delfi-PQ.xml", "Radio")


# open the data file
with open(INPUT_FILE, encoding="utf-8") as input_file:
    data = json.load(input_file)

    # sort messages in chronological order
    data.sort(key=lambda x: x["timestamp"])

    # process each frame
    for frame in data:
        try:
            store_frame(parser=parser, frame=frame)
        except XTCEException as ex:
            # ignore
            pass


# sample query in flux
# from(bucket: "delfi_pq")
#   |> range(start: 2022-01-12T21:12:05Z, stop: 2022-08-17T21:12:05Z)
#   |> filter(fn: (r) => r["_measurement"] == "delfi_pq_eps")
#   |> filter(fn: (r) => r["_field"] == "MCUTemp")
#   |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
#   |> yield(name: "mean")
