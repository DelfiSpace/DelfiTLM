"""Methods recording timestamps of newly added data, used for more targeted processing."""
import os
from datetime import datetime, timedelta
import json
from transmission.processing.satellites import TIME_FORMAT

TIME_RANGE_FILES_DIR = "transmission/processing/temp/"


def get_new_data_file_path(satellite: str, link: str) -> str:
    """Return filepath of the new data time range file."""
    return TIME_RANGE_FILES_DIR + satellite + "/" + satellite + "_" + link + ".json"


def get_failed_data_file_path(satellite: str, link: str) -> str:
    """Return filepath of the time range file storing the interval ."""
    return TIME_RANGE_FILES_DIR + satellite + "/" + "failed" + "_" + link + ".json"


def get_new_data_scraper_temp_folder(satellite: str) -> str:
    """Return filepath of the scraper process temp time range files."""
    return TIME_RANGE_FILES_DIR + satellite + "/scraper/"


def get_new_data_buffer_temp_folder(satellite: str) -> str:
    """Return filepath of the buffer process temp time range files."""
    return TIME_RANGE_FILES_DIR + satellite + "/buffer/"


def read_time_range_file(input_file: str) -> dict:
    """Read time range file and return contents as dictionary."""
    new_data_time_range = {}
    with open(input_file, "r", encoding="utf-8") as file:
        new_data_time_range = json.load(file)

    return new_data_time_range


def save_timestamps_to_file(timestamps: dict, input_file: str) -> None:
    """Dump timestamps to the input file in json format."""
    with open(input_file, "w", encoding="utf-8") as file:
        file.write(json.dumps(timestamps, indent=4))


def reset_new_data_timestamps(satellite: str, link: str, input_file: str) -> None:
    """Replace timestamps form the json given by the input file with []."""
    new_data_time_range = read_time_range_file(input_file)
    new_data_time_range[satellite][link] = []

    with open(input_file, "w", encoding="utf-8") as file:
        file.write(json.dumps(new_data_time_range, indent=4))


def include_timestamp_in_time_range(satellite: str, link: str, timestamp,
                                    input_file: str = None, existing_range: dict = None) -> dict:
    """This function ensures that a given timestamp will be included in the
    time range such that it can then be processed and parsed from raw form.
    The range can be maintained in memory given an existing_range or in file given an input_file."""

    if isinstance(timestamp, str):
        time = datetime.strptime(timestamp, TIME_FORMAT)
    else:
        time = timestamp

    start_time = (time - timedelta(seconds=1)).strftime(TIME_FORMAT)
    end_time = (time + timedelta(seconds=1)).strftime(TIME_FORMAT)

    time_range = (start_time, end_time)

    return update_new_data_timestamps(satellite, link, time_range, input_file, existing_range)


def update_new_data_timestamps(satellite: str, link: str, new_time_range: tuple,
                               input_file: str = None, existing_range: dict = None) -> dict:
    """Bookkeep time range of unprocessed telemetry.
     If an input_file is specified, the timestamps from the file, will be updated and dumped.
     If the existing_range is specified, it will be updated and returned as a dictionary.
     If both input_file and existing_range are specified, an exception is raised."""

    if input_file is not None and existing_range is not None:
        raise RuntimeError("Specify either input_file or existing_range, not both.")

    start_time = new_time_range[0]
    end_time = new_time_range[1]

    if input_file is not None:
        new_data_time_range = read_time_range_file(input_file)

    elif existing_range in [{}, None]:
        new_data_time_range = {}
        new_data_time_range[satellite] = {}
        new_data_time_range[satellite][link] = []
    else:
        new_data_time_range = existing_range

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
    if input_file is not None:
        with open(input_file, "w", encoding="utf-8") as file:
            json.dump(new_data_time_range, file, indent=4)

    return new_data_time_range


def combine_time_ranges(satellite: str, link: str) -> None:
    """Combine time ranges of new data from all processes (buffer processing and scraper)."""
    scraper_folder = get_new_data_scraper_temp_folder(satellite)
    buffer_folder = get_new_data_buffer_temp_folder(satellite)

    for folder in [scraper_folder, buffer_folder]:

        for temp_file in os.listdir(folder):
            if link in temp_file:
                new_data_time_range = read_time_range_file(folder + temp_file)
                new_data_overview_file = get_new_data_file_path(satellite, link)
                include_timestamp_in_time_range(satellite, link,
                                                new_data_time_range[satellite][link][0],
                                                input_file=new_data_overview_file)
                include_timestamp_in_time_range(satellite, link,
                                                new_data_time_range[satellite][link][1],
                                                input_file=new_data_overview_file)
                os.remove(folder + temp_file)
