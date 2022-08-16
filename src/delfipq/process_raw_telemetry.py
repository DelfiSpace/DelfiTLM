"""Script to store Delfi-PQ telemetry frames"""
# pylint: disable=E0401, W0621
import importlib.util
from XTCEParser import XTCEParser, XTCEException

BUCKET = "delfi_pq"

def module_from_file(module_name, file_path):
    """Import module form file"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

tlm_scraper = module_from_file("tlm_scraper", "src/transmission/telemetry_scraper.py")

write_api, query_api = tlm_scraper.get_influx_db_read_and_query_api()

def store_frame(parser, timestamp, frame, observer):
    """Store frame in influxdb"""

    telemetry = parser.processTMFrame(bytes.fromhex(frame))

    if "frame" in telemetry:
        tlm_frame_type = telemetry["frame"]
        tags = {
            # "norad_cat_id": frame["norad_cat_id"],
            # "observer": frame["observer"],
            # "sat_id": frame["sat_id"],
            # "version": frame["version"]
        }
        db_fields = {
            "measurement": "DelfiPQ" + tlm_frame_type,
            "time": timestamp,
            "tags": tags,
            "fields": {
                "observer": observer,
            }
        }
        for field, value in telemetry.items():
            # try to convert to float
            try:
                value = float(value)
                # add ERROR/WARNING/NOMINAL tags
                #     db_fields["tags"]["tag"] = "Err"
            except ValueError:
                pass

            db_fields["fields"][field] = value

            write_api.write(BUCKET, tlm_scraper.INFLUX_ORG, db_fields)
            print(db_fields)
            db_fields["fields"] = {}



parser = XTCEParser("src/delfipq/Delfi-PQ.xml", "Radio")

scraped_telemetry = tlm_scraper.read_scraped_tlm()
LINK = "downlink"

if scraped_telemetry['delfi_pq'] != []:

    start_time = scraped_telemetry["delfi_pq"][LINK][1]
    end_time = scraped_telemetry["delfi_pq"][LINK][0]

    get_unprocessed_frames_query = f'''
    from(bucket: "{BUCKET + "_" + LINK +  "_raw_data"}")
    |> range(start: {start_time}, stop: {end_time})
    |> filter(fn: (r) => r["_field"] == "processed" and r["_value"] == false or
                r["_field"] == "frame" or r["_field"] == "observer")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    data = query_api.query_data_frame(query=get_unprocessed_frames_query)
    # process each frame
    for _, frame in data.iterrows():
        try:
            store_frame(parser, frame["_time"], frame["frame"], frame["observer"])
            frame["processed"] = True
            tlm_scraper.write_frame_to_raw_bucket(
                write_api,
                "delfi_pq_" + LINK,
                frame["_time"],
                frame
                )
        except XTCEException as ex:
            # ignore
            pass

    tlm_scraper.reset_scraped_tlm_timestamps("delfi_pq")
