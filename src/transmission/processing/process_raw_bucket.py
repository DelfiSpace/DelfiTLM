"""Script to store satellite telemetry frames"""
import string
import time
import traceback
from transmission.processing.XTCEParser import SatParsers, XTCEException
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


def parse_and_store_frame(parsers: SatParsers, satellite: str, timestamp: str, frame: str, observer: str, link: str) -> None:
    """Store parsed frame in influxdb"""

    parser = parsers.parsers[satellite]
    #logger.debug("%s: frame: %s", satellite, frame)
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

            try:
                db_fields["fields"][field] = value
                db_fields["tags"]["status"] = status

                write_api.write(bucket, INFLUX_ORG, db_fields)
            except :
                logger.info(db_fields)
                raise

            db_fields["fields"] = {}
            db_fields["tags"] = {}

        #logger.info("%s: processed frame stored. Frame timestamp: %s, link: %s, bucket: %s",
        #            satellite, timestamp, link, bucket)


def mark_processed_flag(satellite: str, link: str, timestamp: str, value: bool) -> None:
    """Write the processed flag to either True or False."""
    write_frame_to_raw_bucket(write_api, satellite, link, timestamp, {'processed': value})


def mark_invalid_flag(satellite: str, link: str, timestamp: str, value: bool) -> None:
    """Write the invalid flag to either True or False."""
    write_frame_to_raw_bucket(write_api, satellite, link, timestamp, {'invalid': value})


# pylint: disable=R0914
def process_retrieved_frames(parsers: SatParsers, satellite: str, link: str, start_time: str, end_time: str,
                             skip_processed: bool = True) -> tuple:
    """Parse frames, store the parsed form and mark the raw entry as processed.
    Return the total number of frames attempting to process and
    how many frames were successfully processed.
    Skip_processed=True will skip over the already processed frames."""

    radio_amateur = 'observer'
    if link == 'uplink':
        radio_amateur = 'operator'

    # TODO: we need to still check the frames where processing failed

    get_unprocessed_frames_query = f'''
        from(bucket: "{satellite + "_raw_data"}")
        |> range(start: {start_time}, stop: {end_time})
        |> filter(fn: (r) => r._measurement == "{satellite + "_" + link + "_raw_data"}")
        |> filter(fn: (r) => r["_field"] == "processed" or
                r["_field"] == "frame" or
                r["_field"] == "{radio_amateur}")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

    if skip_processed == True:
        get_unprocessed_frames_query = get_unprocessed_frames_query + f'''
        |> filter(fn: (r) => r["processed"] == false)
        '''

    # limit the maximum numbr of frames processed per round
    get_unprocessed_frames_query = get_unprocessed_frames_query + f'''
        |> limit(n:100, offset: 0)
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
            # store processed frame
            parse_and_store_frame(parsers, satellite, row["_time"], row["frame"], row[radio_amateur], link)
            # mark raw frame as processed
            mark_processed_flag(satellite, link, row["_time"], True)
            # mark raw frame as valid
            mark_invalid_flag(satellite, link, row["_time"], False)
            processed_frames_count += 1

        except XTCEException as ex:
            logger.error("%s: frame processing error: %s (%s)", satellite, ex, row["frame"])
            # mark raw frame as processed
            mark_processed_flag(satellite, link, row["_time"], True)
            # mark frame as invalid
            mark_invalid_flag(satellite, link, row["_time"], True)
            failed_processing_count += 1

        except Exception as ex:
            logger.error("%s: frame storage error: %s (%s)", satellite, ex, row["frame"])
            logger.error(traceback.format_exc())
            # mark raw frame as processed
            mark_processed_flag(satellite, link, row["_time"], True)
            # mark frame as invalid
            mark_invalid_flag(satellite, link, row["_time"], True)
            failed_processing_count += 1

    return processed_frames_count, total_frames_count


def process_raw_bucket(satellite: str, link: str = None, all_frames: bool = False, failed: bool = False):
    """Trigger bucket processing or reprocessing given satellite."""
    # if link is None process both uplink and downlink, otherwise process only specified link
   
    total_processed_frames = 0
    iterations = 0

    parsers = SatParsers()

    # once the last frame has been processed, maintain the task active for
    # at least 10 seconds while looking for more frames to process
    while iterations < 50:
        time.sleep(0.2)
    
        total_processed_frames = 0

        if link in ["uplink", "downlink"]:
            processed_frames_count, total_frames_count = _process_raw_bucket(parsers, satellite, link, all_frames, failed)
            total_processed_frames += processed_frames_count 
        else:
            processed_frames_count, total_frames_count = _process_raw_bucket(parsers, satellite, "uplink", all_frames, failed)
            total_processed_frames += processed_frames_count
            processed_frames_count, total_frames_count = _process_raw_bucket(parsers, satellite, "downlink", all_frames, failed)
            total_processed_frames += processed_frames_count

        # one more iteration
        iterations += 1
        logger.info("Frames " + str(total_processed_frames) + " Iterations " + str(iterations))

        if total_processed_frames != 0:
            # frames were processed in this iteration, reset the iteration counter
            iterations = 0


def _process_raw_bucket(parsers: SatParsers, satellite: str, link: str, all_frames: bool, failed: bool) -> tuple:
    """Trigger bucket processing given satellite and link.
    all_frames=True will process the entire bucket and failed=True will process only failed frames.
    When both flags are True all frames will be processed."""

    # process the entire bucket
    if all_frames:
        return process_retrieved_frames(parsers, satellite, link, "0", "now()", skip_processed=False)
    else:
        return process_retrieved_frames(parsers, satellite, link, "0", "now()", skip_processed=True)

    processed_frames_count = 0
    total_frames_count = 0

    return processed_frames_count, total_frames_count

