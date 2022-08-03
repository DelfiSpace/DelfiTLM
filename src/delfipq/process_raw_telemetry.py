"""Script to store Delfi-PQ telemetry frames"""
# pylint: disable=E0401, W0621
import importlib.util
from XTCEParser import XTCEParser, XTCEException

SATELLITE = "delfi_pq"
parser = XTCEParser("src/delfipq/Delfi-PQ.xml", "Radio")

def module_from_file(module_name, file_path):
    """Import module form file"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

tlm_scraper = module_from_file("tlm_scraper", "src/transmission/telemetry_scraper.py")

write_api, query_api = tlm_scraper.get_influx_db_read_and_query_api()

def store_frame(timestamp, frame, observer, link):
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

            write_api.write(SATELLITE + "_" + link, tlm_scraper.INFLUX_ORG, db_fields)
            print(db_fields)
            db_fields["fields"] = {}


def process_frames_delfi_pq(link):
    scraped_telemetry = tlm_scraper.read_scraped_tlm()

    if scraped_telemetry[SATELLITE] != []:

        start_time = scraped_telemetry[SATELLITE][link][1]
        end_time = scraped_telemetry[SATELLITE][link][0]

        get_unprocessed_frames_query = f'''
        from(bucket: "{SATELLITE +  "_raw_data"}")
        |> range(start: {start_time}, stop: {end_time})
        |> filter(fn: (r) => r._measurement == "{SATELLITE + "_" + link + "_raw_data"}" and
                    r["_field"] == "processed" and r["_value"] == false or
                    r["_field"] == "frame" or r["_field"] == "observer")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        # query result as dataframe
        df = query_api.query_data_frame(query=get_unprocessed_frames_query)
        # convert dataframe to dict and only include the frame and observer columns
        df_as_dict = df.loc[:, df.columns.isin(['frame', 'observer'])].to_dict(orient='records')
        # process each frame
        for i, row in df.iterrows():
            try:
                store_frame(row["_time"], row["frame"], row["observer"],  link)
                row["processed"] = True
                tlm_scraper.write_frame_to_raw_bucket(
                    write_api,
                    SATELLITE,
                    link,
                    row["_time"],
                    df_as_dict[i]
                    )
            except XTCEException as ex:
                # ignore
                pass

        tlm_scraper.reset_scraped_tlm_timestamps(SATELLITE)

process_frames_delfi_pq("downlink")

