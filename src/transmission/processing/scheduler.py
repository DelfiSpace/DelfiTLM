"""Scheduler for planning telemetry scrapes and frame processing"""
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from transmission.processing.process_raw_bucket import process_raw_bucket
from transmission.processing.telemetry_scraper import scrape
from transmission.processing.save_raw_data import process_uplink_and_downlink
# Trigger:
    # date: use when you want to run the job just once at a certain point of time
    # interval: use when you want to run the job at fixed intervals of time
    # cron: use when you want to run the job periodically at certain time(s) of day


job_defaults = {
    'coalesce': False,
    'max_instances': 1
}

scheduler = BackgroundScheduler( job_defaults=job_defaults)

def get_job_id(satellite, job_description, link=None):

    if link is None:

        return satellite + "_" + job_description + "_"

    return satellite + "_" + link + "_" + job_description + "_"


def schedule_job(satellite, job_type, link, trigger=None, minutes=None):
    job_id = get_job_id(satellite, job_type, link)
    if job_type == "scraper":
        args = [satellite]
        add_job(scrape, args, job_id, trigger=trigger, minutes=minutes)

    elif job_type == "buffer_processing":
        args = []
        add_job(process_uplink_and_downlink, args, job_id, trigger=trigger, minutes=minutes)

    elif job_type == "raw_bucket_processing":
        args = [satellite, link]
        add_job(process_raw_bucket, args, job_id, trigger=trigger, minutes=minutes)


def get_running_jobs():
    job_ids = []

    for job in scheduler.get_jobs():
        job_ids.append(job.id)

    return job_ids


def add_job(function, args, job_id, trigger=None, minutes=None):

    if scheduler.get_job(job_id) is None:
        scheduler.add_job(
            function,
            args=args,
            id=job_id,
            max_instances=1
        )
    else:
        scheduler.reschedule_job(job_id, trigger="date")


def start():
    """Start the background scheduler"""

    # add_scraper_job("delfi_pq", trigger="interval", minutes=60*12)
    # add_scraper_job("delfi_next", trigger="interval", minutes=60*12)
    # add_scraper_job("delfi_c3", trigger="interval", minutes=60*12)
    # add_scraper_job("da_vinci", trigger="interval", minutes=60*12)


    scheduler.start()


def stop():
    """Stop the scheduler"""
    scheduler.shutdown()
