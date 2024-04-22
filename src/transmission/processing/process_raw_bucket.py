"""Script to store satellite telemetry frames"""
import string
import time
import traceback
from transmission.processing.XTCEParser import SatParsers, XTCEException
from transmission.processing.influxdb_api import influxdb_api
from django_logger import logger


def parse_and_store_frame(parsers: SatParsers, db: influxdb_api, satellite: str, timestamp: str, frame: str,
        link: str) -> None:
    """Store parsed frame in influxdb"""

    parser = parsers.parsers[satellite]

    telemetry = parser.processTMFrame(bytes.fromhex(frame))
    bucket = satellite + "_" + link

    if "frame" in telemetry:
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

            db.save_processed_frame(satellite, link, telemetry["frame"], timestamp, {"status": status}, {field: value})


def process_retrieved_frames(parsers: SatParsers, db: influxdb_api, satellite: str, link: str) -> int:
    """Parse frames, store the parsed form and mark the raw entry as processed.
    Return the total number of frames attempting to process and
    how many frames were successfully processed.
    Skip_processed=True will skip over the already processed frames."""

    frames_list = db.get_raw_frames_to_process(satellite, link)

    processed_frames_count = 0

    # process each frame
    for _, row in frames_list.iterrows():
        try:
            # store processed frame
            parse_and_store_frame(parsers, db, satellite, row["_time"], row["frame"], link)
            # mark raw frame as processed and valid
            db.update_raw_frame(satellite, link, row["_time"], {'processed': True, 'invalid': False})
            processed_frames_count += 1

        except XTCEException as ex:
            logger.error("%s: frame processing error: %s (%s)", satellite, ex, row["frame"])
            logger.error(traceback.format_exc())
            # mark raw frame as processed and invalid
            db.update_raw_frame(satellite, link, row["_time"], {'processed': True, 'invalid': True})

        # indeed a very broad exception, but it keeps the processor running in case of rogue frames
        except Exception as ex:       # pylint: disable=broad-except
            logger.error("%s: frame storage error: %s (%s)", satellite, ex, row["frame"])
            logger.error(traceback.format_exc())
            logger.info("Problematic frame: " + str(row)) 
            logger.info(row)
            # mark raw frame as processed and invalid
            db.update_raw_frame(satellite, link, row["_time"], {'processed': True, 'invalid': True})

    return processed_frames_count


def process_raw_bucket(satellite: str, link: str = None, all_frames: bool = False, failed: bool = False):
    """Bucket processing or reprocessing task."""
    # if link is None process both uplink and downlink, otherwise process only specified link

    total_processed_frames = 0
    iterations = 0

    parsers = SatParsers()
    db = influxdb_api()

    # TODO handle reprocessing failed frames

    # once the last frame has been processed, maintain the task active for
    # at least 10 seconds while looking for more frames to process
    while iterations < 50:
        total_processed_frames = 0

        if link in ["uplink", "downlink"]:
            processed_frames_count = process_retrieved_frames(parsers, db, satellite, link)
            total_processed_frames += processed_frames_count
        else:
            processed_frames_count = process_retrieved_frames(parsers, db, satellite, "uplink")
            total_processed_frames += processed_frames_count
            processed_frames_count = process_retrieved_frames(parsers, db, satellite, "downlink")
            total_processed_frames += processed_frames_count

        # one more iteration
        iterations += 1

        if total_processed_frames != 0:
            # frames were processed in this iteration, reset the iteration counter
            iterations = 0
            logger.info("Processed " + str(total_processed_frames) + " frames")

        # maintain the thread alive and re-check if new frames have been received
        time.sleep(0.2)
