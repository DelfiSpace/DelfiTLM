"""Script to store satellite telemetry frames"""
import os
import string
from transmission.processing import XTCEParser as xtce_parser
from django_logger import logger
import transmission.processing.bookkeep_new_data_time_range as time_range
from transmission.processing.influxdb_api import INFLUX_ORG, commit_frame, \
get_influx_db_read_and_query_api, write_frame_to_raw_bucket

write_api, query_api = get_influx_db_read_and_query_api()

def store_raw_frame(satellite: str, timestamp, frame: str, observer: str, link: str) -> bool:
    """Store raw unprocessed frame in influxdb"""
    frame_fields = {
        "frame": frame,
        "observer": observer,
        "timestamp": timestamp,
        "processed": False
    }

    stored = commit_frame(write_api, query_api, satellite, link, frame_fields)
    if stored:
        file = time_range.get_new_data_file_path(satellite, link)
        time_range.include_timestamp_in_time_range(satellite, link, timestamp, file)
    return stored


def parse_and_store_frame(satellite: str, timestamp: str, frame: str, observer: str, link: str) -> None:
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

def mark_processed_flag(satellite: str, link: str, timestamp: str, value: bool) -> None:
    """Write the processed flag to either True or False."""
    write_frame_to_raw_bucket( write_api, satellite, link, timestamp, {'processed': value})

def process_retrieved_frames(satellite: str, link: str, start_time: str, end_time: str) -> tuple:

    processed_frames_count = 0
    total_frames_count = 0

    radio_amateur = 'observer'
    if link == 'uplink':
        radio_amateur = 'operator'

    get_unprocessed_frames_query = f'''
        from(bucket: "{satellite +  "_raw_data"}")
        |> range(start: {start_time}, stop: {end_time})
        |> filter(fn: (r) => r._measurement == "{satellite + "_" + link + "_raw_data"}")
        |> filter(fn: (r) => r["_field"] == "processed" or
                r["_field"] == "frame" or
                r["_field"] == "{radio_amateur}")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
    # query result as dataframe
    dataframe = query_api.query_data_frame(query=get_unprocessed_frames_query)
    dataframe = dataframe.reset_index()
    # process each frame
    for _, row in dataframe.iterrows():
        total_frames_count += 1
        try:
            if row["processed"]: # skip frame if it's processed
                continue
            # store processed frame
            parse_and_store_frame(satellite,row["_time"],row["frame"],row[radio_amateur],link)
            # mark raw frame as processed
            mark_processed_flag(satellite, link, row["_time"], True)
            processed_frames_count += 1

        except xtce_parser.XTCEException as ex:
            logger.error("%s: frame processing error: %s (%s)", satellite, ex, row["frame"])
            time_range.include_timestamp_in_time_range(satellite,
                                                        link,
                                                        row["_time"],
                                                        time_range.FAILED_PROCESSING_FILE
                                                        )
            # mark frame as unprocessed
            mark_processed_flag(satellite, link, row["_time"], False)

        logger.info("%s: %s data was processed from %s - %s; %s out of %s were successfully processed",\
            satellite, link, start_time, end_time, processed_frames_count, total_frames_count)

        if total_frames_count == 0:
            logger.info("%s: no frames to process", satellite)

        return processed_frames_count, total_frames_count


def process_raw_bucket(satellite: str, link: str, all_frames: bool=False, failed: bool=False) -> tuple:
    """Parse frames, store the parsed form and mark the raw entry as processed.
    Return the total number of frames attempting to process and
    how many frames were successfully processed."""

    combine_time_ranges(satellite, link)

    if all_frames:
        return process_retrieved_frames(satellite, link, "0", "now()")

    file = time_range.get_new_data_file_path(satellite, link)
    new_data_time_range = time_range.read_time_range_file(file)

    if new_data_time_range[satellite][link] != []:

        start_time = new_data_time_range[satellite][link][0]
        end_time = new_data_time_range[satellite][link][1]
        processed_frames_count, total_frames_count = \
            process_retrieved_frames(satellite, link, start_time, end_time)


        time_range.reset_new_data_timestamps(satellite, link, file)

    return processed_frames_count, total_frames_count


def combine_time_ranges(satellite: str, link: str) -> None:
    scraper_folder = time_range.get_new_data_scraper_temp_folder(satellite)
    buffer_folder = time_range.get_new_data_buffer_temp_folder(satellite)

    for folder in [scraper_folder, buffer_folder]:

        for temp_file in os.listdir(folder):
            if link in temp_file:
                new_data_time_range = time_range.read_time_range_file(folder + temp_file)
                new_data_overview_file = time_range.get_new_data_file_path(satellite, link)
                time_range.include_timestamp_in_time_range(satellite, link,
                                                           new_data_time_range[satellite][link][0],
                                                           input_file=new_data_overview_file)
                time_range.include_timestamp_in_time_range(satellite, link,
                                                           new_data_time_range[satellite][link][1],
                                                           input_file=new_data_overview_file)
                os.remove(folder + temp_file)
