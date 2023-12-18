"""Script to store satellite telemetry frames"""
import string
from transmission.processing import XTCEParser as xtce_parser
from django_logger import logger
import transmission.processing.bookkeep_new_data_time_range as time_range
from transmission.processing.influxdb_api import INFLUX_ORG, commit_frame, \
    get_influx_db_read_and_query_api, write_frame_to_raw_bucket

write_api, query_api = get_influx_db_read_and_query_api()


def store_raw_frame(satellite: str, timestamp: str, frame: str, observer: str, link: str) -> bool:
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
    logger.debug("%s: frame: %s", satellite, frame)
    telemetry = parser.processTMFrame(bytes.fromhex(frame))
    bucket = satellite + "_" + link

    if "frame" in telemetry:
        sat_name_pascal_case = string.capwords(satellite.replace("_", " ")).replace(" ", "")
        tags = {}

        db_fields = {

            "measurement": sat_name_pascal_case + telemetry["frame"],
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

            write_api.write(bucket, INFLUX_ORG, db_fields)
            # print(db_fields)
            db_fields["fields"] = {}
            db_fields["tags"] = {}

        logger.info("%s: processed frame stored. Frame timestamp: %s, link: %s, bucket: %s",
                    satellite, timestamp, link, bucket)


def mark_processed_flag(satellite: str, link: str, timestamp: str, value: bool) -> None:
    """Write the processed flag to either True or False."""
    write_frame_to_raw_bucket(write_api, satellite, link, timestamp, {'processed': value})


# pylint: disable=R0914
def process_retrieved_frames(satellite: str, link: str, start_time: str, end_time: str,
                             skip_processed: bool = True) -> tuple:
    """Parse frames, store the parsed form and mark the raw entry as processed.
    Return the total number of frames attempting to process and
    how many frames were successfully processed.
    Skip_processed=True will skip over the already processed frames."""

    radio_amateur = 'observer'
    if link == 'uplink':
        radio_amateur = 'operator'

    get_unprocessed_frames_query = f'''
        from(bucket: "{satellite + "_raw_data"}")
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

    failed_processing_count = 0
    processed_frames_count = 0
    total_frames_count = 0
    # process each frame
    for _, row in dataframe.iterrows():
        total_frames_count += 1
        try:
            if row["processed"] and skip_processed:  # skip frame if it's processed
                logger.info("%s: frame skipped (already processed): %s ", satellite, row["frame"])
                continue
            # store processed frame
            parse_and_store_frame(satellite, row["_time"], row["frame"], row[radio_amateur], link)
            # mark raw frame as processed
            mark_processed_flag(satellite, link, row["_time"], True)
            processed_frames_count += 1

        except xtce_parser.XTCEException as ex:
            logger.error("%s: frame processing error: %s (%s)", satellite, ex, row["frame"])
            time_range.include_timestamp_in_time_range(satellite,
                                                       link,
                                                       row["_time"],
                                                       time_range.get_failed_data_file_path(satellite, link)
                                                       )
            # mark frame as unprocessed
            mark_processed_flag(satellite, link, row["_time"], False)
            failed_processing_count += 1

    skipped_frames_count = total_frames_count - processed_frames_count - failed_processing_count

    frames_status = f"out of {total_frames_count} frames: " + \
                    f"{processed_frames_count} were successfully parsed, " + \
                    f"{skipped_frames_count} were skipped, and " + \
                    f"{failed_processing_count} failed."

    logger.info("%s: %s frames processed from %s - %s; %s", satellite, link, start_time, end_time, frames_status)

    if total_frames_count == 0:
        logger.info("%s: no frames to process", satellite)

    return processed_frames_count, total_frames_count


def process_raw_bucket(satellite: str, link: str = None, all_frames: bool = False, failed: bool = False):
    """Trigger bucket processing or reprocessing given satellite."""
    # if link is None process both uplink and downlink, otherwise process only specified link

    if link in ["uplink", "downlink"]:
        _process_raw_bucket(satellite, link, all_frames, failed)
    else:
        _process_raw_bucket(satellite, "uplink", all_frames, failed)
        _process_raw_bucket(satellite, "downlink", all_frames, failed)



def _process_raw_bucket(satellite: str, link: str, all_frames: bool, failed: bool) -> tuple:
    """Trigger bucket processing given satellite and link.
    all_frames=True will process the entire bucket and failed=True will process only failed frames.
    When both flags are True all frames will be processed."""

    time_range.combine_time_ranges(satellite, link)

    # process the entire bucket
    if all_frames:
        return process_retrieved_frames(satellite, link, "0", "now()", skip_processed=False)
    # process frames in the failed frames time range
    if failed:
        file = time_range.get_failed_data_file_path(satellite, link)
        new_data_time_range = time_range.read_time_range_file(file)
    # process frames in the new data time range (newly ingested data)
    else:
        file = time_range.get_new_data_file_path(satellite, link)
        new_data_time_range = time_range.read_time_range_file(file)

    processed_frames_count = 0
    total_frames_count = 0

    # if the time range is empty there are no frames to process
    if new_data_time_range[satellite][link] != []:

        start_time = new_data_time_range[satellite][link][0]
        end_time = new_data_time_range[satellite][link][1]
        processed_frames_count, total_frames_count = process_retrieved_frames(satellite, link, start_time, end_time)

        # don't reset the interval of failed frames, unless reprocessing was successful
        if failed is False or processed_frames_count == total_frames_count:
            time_range.reset_new_data_timestamps(satellite, link, file)
    else:
        logger.info("%s: no frames to process", satellite)
    return processed_frames_count, total_frames_count
