"""Scheduler for planning telemetry scrapes and frame processing and
 methods for adding frame processing jobs to the scheduler.
Scraping, buffer processing and bucket processing can be parallelized.
Limitations:
- Duplicate tasks are not considered.
- Each satellite can have only 1 bucket processing job scheduled out of the following:
    - raw_bucket_processing
    - reprocess_entire_raw_bucket
    - reprocess_failed_raw_bucket
"""
import datetime
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_JOB_EXECUTED, EVENT_JOB_SUBMITTED
from django_logger import logger
from transmission.processing.satellites import SATELLITES
from transmission.processing.process_raw_bucket import process_raw_bucket
from transmission.processing.telemetry_scraper import scrape
from transmission.processing.save_raw_data import process_uplink_and_downlink


def get_job_id(satellite: str, job_description: str) -> str:
    """Create an id, job description"""

    if "bucket" in job_description:
        return satellite + "_bucket_processing"

    return satellite + "_" + job_description


def remove_job(satellite: str, job_type: str):
    """Remove job from schedule"""
    job_id = get_job_id(satellite, job_type)
    scheduler = Scheduler()
    scheduler.remove_job_from_schedule(job_id)


def schedule_job(satellite: str, job_type: str, link: str,
                 date: datetime = None, interval: int = None) -> None:
    """Schedule job"""
    scheduler = Scheduler()

    if job_type == "scraper":
        args = [satellite]
        job_id = get_job_id(satellite, job_type)
        scheduler.add_job_to_schedule(scrape, args, job_id, date, interval)

    elif job_type == "buffer_processing":
        args = []
        job_id = job_type
        scheduler.add_job_to_schedule(process_uplink_and_downlink, args, job_id, date, interval)

    elif job_type == "raw_bucket_processing":
        args = [satellite, link]
        job_id = get_job_id(satellite, job_type)
        scheduler.add_job_to_schedule(process_raw_bucket, args, job_id, date, interval)

    elif job_type == "reprocess_entire_raw_bucket":
        args = [satellite, link, True, False]
        job_id = get_job_id(satellite, job_type)
        scheduler.add_job_to_schedule(process_raw_bucket, args, job_id, date, interval)

    elif job_type == "reprocess_failed_raw_bucket":
        args = [satellite, link, False, True]
        job_id = get_job_id(satellite, job_type)
        scheduler.add_job_to_schedule(process_raw_bucket, args, job_id, date, interval)


class Singleton(type):
    """Singleton class"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Scheduler(metaclass=Singleton):
    """Scheduler implementing the singleton design pattern, i.e.
    multiple instantiations will point to the same object."""

    # Scheduler workflow: add job -> remove job -> submit job -> execute job
    # Task Triggers:
    # date: use when you want to run the job just once at a certain point of time
    # interval: use when you want to run the job at fixed intervals of time
    # cron: use when you want to run the job periodically at certain time(s) of day

    __instance = None

    @staticmethod
    def get_instance():
        """ Returns class instance"""
        return Scheduler.__instance

    def __init__(self) -> None:
        if Scheduler.__instance is not None:
            logger.info("Scheduler already instantiated")
        else:
            executors = {
                'default': ThreadPoolExecutor(1),
                # 'processpool': ProcessPoolExecutor(0)
            }
            job_defaults = {
                'coalesce': True,
                'max_instances': 1
            }

            self.running_jobs = set()
            self.pending_jobs = set()

            self.scheduler = BackgroundScheduler(job_defaults=job_defaults, executors=executors)

            self.scheduler.add_listener(self.submitted_job_listener, EVENT_JOB_SUBMITTED)
            self.scheduler.add_listener(self.executed_job_listener, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self.add_job_listener, EVENT_JOB_ADDED)
            self.scheduler.add_listener(self.remove_job_listener, EVENT_JOB_REMOVED)

            Scheduler.__instance = self

            self.start_scheduler()

    def add_job_listener(self, event) -> None:
        """Listens to newly added jobs"""
        logger.info("Scheduler added job: %s", event.job_id)
        self.pending_jobs.add(event.job_id)

    def remove_job_listener(self, event) -> None:
        """Listens to removed jobs"""
        logger.info("Scheduler removed job: %s", event.job_id)
        self.pending_jobs.remove(event.job_id)

    def executed_job_listener(self, event) -> None:
        """Listens to executed jobs"""
        logger.info("Scheduler executed job: %s", event.job_id)
        self.running_jobs.remove(event.job_id)

        # automated processing pipeline:
        # - when a buffer processing task completes that will trigger the raw bucket processing
        # - when a scraper task completes that will trigger the raw bucket processing
        if "buffer_processing" in event.job_id:
            for sat in SATELLITES:
                schedule_job(sat, "raw_bucket_processing", "uplink")
                schedule_job(sat, "raw_bucket_processing", "downlink")

        elif "scraper" in event.job_id:
            for sat in SATELLITES:
                if sat in event.job_id:
                    schedule_job(sat, "raw_bucket_processing", "downlink")

    def submitted_job_listener(self, event) -> None:
        """Listens to submitted jobs"""
        self.running_jobs.add(event.job_id)
        logger.info("Scheduler submitted job: %s", event.job_id)

    def get_pending_jobs(self) -> set:
        """Get the ids of the currently scheduled jobs."""
        return self.pending_jobs

    def get_running_jobs(self) -> set:
        """Get the ids of the currently running jobs."""
        return self.running_jobs

    # pylint:disable=R0913
    def add_job_to_schedule(self, function: Callable, args: list, job_id: str,
                            date: datetime = None, interval: int = None) -> None:
        """Add a job to the schedule if not already scheduled."""
        if interval is not None:
            trigger = IntervalTrigger(minutes=interval, start_date=date)
        else:
            trigger = DateTrigger(run_date=date)

        if job_id not in self.running_jobs:
            self.scheduler.add_job(
                function,
                args=args,
                id=job_id,
                trigger=trigger,
            )
        elif job_id in self.pending_jobs:
            self.scheduler.reschedule_job(job_id, trigger=trigger)

    def remove_job_from_schedule(self, job_id: str) -> None:
        """Remove a job to the schedule if it exists."""
        if job_id in self.pending_jobs:
            self.scheduler.remove_job(job_id)

    def start_scheduler(self) -> None:
        """Start the background scheduler"""
        logger.info("Scheduler started")
        self.scheduler.start()

    def stop_scheduler(self) -> None:
        """Stop the scheduler"""
        logger.info("Scheduler shutdown")
        self.scheduler.shutdown()
