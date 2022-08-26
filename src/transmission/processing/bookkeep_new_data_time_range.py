"""Methods recording timestamps of newly added data,
used for more targeted processing."""
from datetime import datetime, timedelta
import json
from transmission.processing.satellites import TIME_FORMAT

FAILED_PROCESSING_FILE = "transmission/processing/time_range_files/failed_processing.json"
TIME_RANGE_FILES_DIR = "transmission/processing/time_range_files/"


def get_new_data_file_path(satellite: str, link: str) -> str:
    """Return filepath of the new data time range file"""
    return TIME_RANGE_FILES_DIR + satellite + "_" + link + ".json"


def read_time_range_file(input_file: str) -> dict:
    """Read scraped_telemetry.json."""
    new_data_time_range = {}
    with open(input_file, "r", encoding="utf-8") as file:
        new_data_time_range = json.load(file)

    return new_data_time_range


def reset_new_data_timestamps(satellite: str, link: str, input_file: str) -> None:
    """Replace timestamps in scraped_telemetry.json with []."""
    new_data_time_range = read_time_range_file(input_file)
    new_data_time_range[satellite][link] = []

    with open(input_file, "w", encoding="utf-8") as file:
        file.write(json.dumps(new_data_time_range, indent=4))


def include_timestamp_in_time_range(satellite: str, link: str, timestamp, input_file:str):
    """This function ensures that a given timestamp will be included in the scraped
    telemetry time range such that it can then be processed and parsed from raw form."""

    if isinstance(timestamp, str):
        time = datetime.strptime(timestamp, TIME_FORMAT)
    else:
        time = timestamp

    start_time = (time - timedelta(seconds=1)).strftime(TIME_FORMAT)
    end_time = (time + timedelta(seconds=1)).strftime(TIME_FORMAT)

    update_new_data_timestamps(satellite, link, start_time, end_time, input_file)


def update_new_data_timestamps(satellite, link, start_time, end_time, input_file) -> None:
    """Bookkeep time range of unprocessed telemetry."""
    new_data_time_range = read_time_range_file(input_file)

    # No time range saved
    if new_data_time_range[satellite][link] == []:
        new_data_time_range[satellite][link] = [start_time, end_time]
    # Update time range
    else:
        new_data_time_range[satellite][link][0] = min(
                                                new_data_time_range[satellite][link][0],
                                                start_time
                                                )
        new_data_time_range[satellite][link][1] = max(
                                                new_data_time_range[satellite][link][1],
                                                end_time
                                                )

    with open(input_file, "w", encoding="utf-8") as file:
        json.dump(new_data_time_range, file, indent=4)
