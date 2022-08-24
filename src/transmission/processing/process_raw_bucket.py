"""Script to store satellite telemetry frames"""
import string
from transmission.processing import XTCEParser as xtce_parser
from django_logger import logger
import transmission.processing.bookkeep_new_data_time_range as time_range
from transmission.processing.influxdb_api import INFLUX_ORG, commit_frame, \
get_influx_db_read_and_query_api, write_frame_to_raw_bucket

from transmission.processing.telemetry_scraper import NEW_DATA_FILE

write_api, query_api = get_influx_db_read_and_query_api()
FAILED_PROCESSING_FILE = "transmission/processing/failed_processing.json"

def store_raw_frame(satellite, timestamp, frame: str, observer: str, link: str):
    """Store raw unprocessed frame in influxdb"""
    frame_fields = {
        "frame": frame,
        "observer": observer,
        "timestamp": timestamp
    }

    stored = commit_frame(write_api, query_api, satellite, link, frame_fields)
    if stored:
        time_range.include_timestamp_in_time_range(satellite, link, timestamp, NEW_DATA_FILE)
    return stored


def store_frame(satellite, timestamp, frame: str, observer: str, link: str):
    """Store parsed frame in influxdb"""

    parser = xtce_parser.SatParsers().parsers[satellite]
    telemetry = parser.processTMFrame(bytes.fromhex(frame))

    if "frame" in telemetry:
        tlm_frame_type = telemetry["frame"]
        sat_name_pascal_case = string.capwords(satellite.replace("_", " ")).replace(" ", "")
        tags = {}

        db_fields = {

            "measurement": sat_name_pascal_case + tlm_frame_type,
            "time": timestamp,
            "tags": tags,
            "fields": {
                "observer": observer,
            }
        }

        for field, value_and_status in telemetry.items():
            # skip frame field
            if field == "frame":
                continue

            value = value_and_status["value"]
            status = value_and_status["status"]
            # try to convert to float
            try:
                value = float(value)
            except ValueError:
                pass

            # print(field + " " + str(value) + " " + status)
            logger.debug("%s: field: %s, val: %s, status: %s", satellite, field, str(value), status)

            db_fields["fields"][field] = value
            db_fields["tags"]["status"] = status

            write_api.write(satellite + "_" + link, INFLUX_ORG, db_fields)
            # print(db_fields)
            db_fields["fields"] = {}
            db_fields["tags"] = {}

        logger.info("%s: processed frame stored. Frame timestamp: %s, link: %s",
                    satellite, timestamp, link)


def process_raw_bucket(satellite, link) -> tuple:
    """Parse frames, store the parsed form and mark the raw entry as processed.
    Return the total number of frames attempting to process and
    how many frames were successfully processed."""

    scraped_telemetry = time_range.read_time_range_file(NEW_DATA_FILE)

    processed_frames_count = 0
    total_frames_count = 0

    if scraped_telemetry[satellite][link] != []:

        start_time = scraped_telemetry[satellite][link][0]
        end_time = scraped_telemetry[satellite][link][1]

        get_unprocessed_frames_query = f'''
        from(bucket: "{satellite +  "_raw_data"}")
        |> range(start: {start_time}, stop: {end_time})
        |> filter(fn: (r) => r._measurement == "{satellite + "_" + link + "_raw_data"}" and
                    r["_field"] == "processed" and r["_value"] == false or
                    r["_field"] == "frame" or r["_field"] == "observer")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        # query result as dataframe
        dataframe = query_api.query_data_frame(query=get_unprocessed_frames_query)
        # convert dataframe to dict and only include the frame and observer columns
        df_as_dict = dataframe.loc[:, dataframe.columns.isin(['frame', 'observer'])]
        df_as_dict = df_as_dict.to_dict(orient='records')
        total_frames_count = len(df_as_dict)

        # process each frame
        for i, row in dataframe.iterrows():
            try:
                store_frame(satellite, row["_time"], row["frame"], row["observer"],  link)
                df_as_dict[i]["processed"] = True
                write_frame_to_raw_bucket(
                    write_api,
                    satellite,
                    link,
                    row["_time"],
                    df_as_dict[i]
                    )
                processed_frames_count += 1
            except xtce_parser.XTCEException as ex:
                logger.exception("%s: frame processing error: %s", satellite, ex)
                time_range.include_timestamp_in_time_range(satellite,
                                                           link,
                                                           row["_time"],
                                                           FAILED_PROCESSING_FILE
                                                           )

        if processed_frames_count == total_frames_count:
            time_range.reset_new_data_timestamps(satellite, NEW_DATA_FILE)
            logger.info("%s: %s data was processed from %s - %s",satellite,link,start_time,end_time)
    else:
        logger.info("%s: no frames to process", satellite)

    return processed_frames_count, total_frames_count
