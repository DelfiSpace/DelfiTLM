"""Scheduler for planning telemetry scrapes and frame processing"""
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ADDED, EVENT_JOB_REMOVED
from transmission.processing.process_raw_bucket import process_raw_bucket
from transmission.processing.telemetry_scraper import scrape
from transmission.processing.save_raw_data import process_uplink_and_downlink
from django_logger import logger

# Trigger:
    # date: use when you want to run the job just once at a certain point of time
    # interval: use when you want to run the job at fixed intervals of time
    # cron: use when you want to run the job periodically at certain time(s) of day

executors = {
    'default': ThreadPoolExecutor(1),
    # 'processpool': ProcessPoolExecutor(0)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 1
}

scheduler = BackgroundScheduler(job_defaults=job_defaults, executors=executors)
running_jobs = set()

def add_job_listener(event):
    """Listens to newly added jobs"""
    running_jobs.add(event.job_id)

def remove_job_listener(event):
    """Listens to removed jobs"""
    running_jobs.remove(event.job_id)

scheduler.add_listener(add_job_listener, EVENT_JOB_ADDED)
scheduler.add_listener(remove_job_listener, EVENT_JOB_REMOVED)


def get_job_id(satellite: str, job_description: str, link: str=None) -> str:
    """Create an id, job description"""
    if link is None:

        return satellite + "_" + job_description

    return satellite + "_" + link + "_" + job_description


def schedule_job(satellite: str, job_type: str, link: str) -> None:

    """Schedule job"""
    if job_type == "scraper":
        args = [satellite]
        job_id = get_job_id(satellite, job_type)
        add_job(scrape, args, job_id)

    elif job_type == "buffer_processing":
        args = []
        job_id = job_type
        add_job(process_uplink_and_downlink, args, job_id)

    elif job_type == "raw_bucket_processing":
        args = [satellite, link]
        job_id = get_job_id(satellite, job_type, link)
        add_job(process_raw_bucket, args, job_id)


def get_pending_jobs() -> list:
    """Get the ids of the currently scheduled jobs."""
    job_ids = []

    for job in scheduler.get_jobs():
        job_ids.append(job.id)

    return job_ids


def add_job(function: Callable, args:list, job_id:str) -> None:
    """Add a job to the schedule if not already scheduled."""
    scheduler.add_job(
            function,
            args=args,
            id=job_id,
        )
    logger.info("Scheduled job: %s", job_id)


def start() -> None:
    """Start the background scheduler"""

    logger.info("Scheduler started")
    # add_scraper_job("delfi_pq", trigger="interval", minutes=60*12)
    # add_scraper_job("delfi_next", trigger="interval", minutes=60*12)
    # add_scraper_job("delfi_c3", trigger="interval", minutes=60*12)
    # add_scraper_job("da_vinci", trigger="interval", minutes=60*12)


    scheduler.start()


def stop() -> None:
    """Stop the scheduler"""

    logger.info("Scheduler shutdown")
    scheduler.shutdown()
