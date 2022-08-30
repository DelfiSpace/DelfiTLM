"""Methods for adding frame processing jobs to the scheduler."""
from transmission.processing.process_raw_bucket import process_raw_bucket
from transmission.processing.telemetry_scraper import scrape
from transmission.processing.save_raw_data import process_uplink_and_downlink
from transmission.scheduler import Scheduler


def get_job_id(satellite: str, job_description: str, link: str=None) -> str:
    """Create an id, job description"""
    if link is None:

        return satellite + "_" + job_description

    return satellite + "_" + link + "_" + job_description


def schedule_job(satellite: str, job_type: str, link: str) -> None:
    """Schedule job"""
    scheduler = Scheduler()

    if job_type == "scraper":
        args = [satellite]
        job_id = get_job_id(satellite, job_type)
        scheduler.add_job_to_schedule(scrape, args, job_id)

    elif job_type == "buffer_processing":
        args = []
        job_id = job_type
        scheduler.add_job_to_schedule(process_uplink_and_downlink, args, job_id)

    elif job_type == "raw_bucket_processing":
        args = [satellite, link]
        job_id = get_job_id(satellite, job_type, link)
        scheduler.add_job_to_schedule(process_raw_bucket, args, job_id)
