"""Script to store Delfi-PQ telemetry frames"""
from transmission import telemetry_scraper as tlm_scraper
from delfipq import XTCEParser as xtce_parser
from django_logger import logger

SATELLITE = "delfi_pq"

write_api, query_api = tlm_scraper.get_influx_db_read_and_query_api()

def store_raw_frame(timestamp, frame: str, observer: str, link: str):
    """Store raw unprocessed frame in influxdb"""
    frame_fields = {
        "frame": frame,
        "observer": observer,
        "timestamp": timestamp
    }

    stored = tlm_scraper.commit_frame(write_api, query_api, SATELLITE, link, frame_fields)
    if stored:
        tlm_scraper.include_timestamp_in_scraped_tlm_range(SATELLITE, link, timestamp)
    return stored

def store_frame(timestamp, frame: str, observer: str, link: str):
    """Store parsed frame in influxdb"""

    parser = xtce_parser.XTCEParser("delfipq/Delfi-PQ.xml", "Radio")
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
            logger.debug("delfi_pq: field: %s, val: %s, status: %s", field, str(value), status)

            db_fields["fields"][field] = value
            db_fields["tags"]["status"] = status

            write_api.write(SATELLITE + "_" + link, tlm_scraper.INFLUX_ORG, db_fields)
            # print(db_fields)
            db_fields["fields"] = {}
            db_fields["tags"] = {}

        logger.info("delfi_pq: processed frame stored. Frame timestamp: %s, link: %s",
                    timestamp, link)



def process_frames_delfi_pq(link) -> tuple:
    """Parse frames, store the parsed form and mark the raw entry as processed.
    Return the total number of frames attempting to process and
    how many frames were successfully processed."""

    scraped_telemetry = tlm_scraper.read_scraped_tlm()

    processed_frames_count = 0
    total_frames_count = 0

    if scraped_telemetry[SATELLITE][link] != []:

        start_time = scraped_telemetry[SATELLITE][link][0]
        end_time = scraped_telemetry[SATELLITE][link][1]

        get_unprocessed_frames_query = f'''
        from(bucket: "{SATELLITE +  "_raw_data"}")
        |> range(start: {start_time}, stop: {end_time})
        |> filter(fn: (r) => r._measurement == "{SATELLITE + "_" + link + "_raw_data"}" and
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
                store_frame(row["_time"], row["frame"], row["observer"],  link)
                df_as_dict[i]["processed"] = True
                tlm_scraper.write_frame_to_raw_bucket(
                    write_api,
                    SATELLITE,
                    link,
                    row["_time"],
                    df_as_dict[i]
                    )
                processed_frames_count += 1
            except xtce_parser.XTCEException as ex:
                logger.exception("delfi_pq: frame processing error: %s", ex)

        if processed_frames_count == total_frames_count:
            tlm_scraper.reset_scraped_tlm_timestamps(SATELLITE)
            logger.info("delfi_pq: %s data was processed from %s - %s", link, start_time, end_time)
    else:
        logger.info("delfi_pq: no frames to process")

    return processed_frames_count, total_frames_count
