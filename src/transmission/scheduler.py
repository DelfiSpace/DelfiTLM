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
from apscheduler.schedulers.base import STATE_STOPPED, STATE_PAUSED, STATE_RUNNING
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_JOB_EXECUTED, \
    EVENT_JOB_SUBMITTED, EVENT_JOB_ERROR
from django.forms import ValidationError
from django_logger import logger
from transmission.processing.satellites import SATELLITES
from transmission.processing.process_raw_bucket import process_raw_bucket
from transmission.processing.telemetry_scraper import scrape
from transmission.processing.save_raw_data import process_uplink_and_downlink
from transmission.processing.XTCEParser import XTCEParser

def get_job_id(satellite: str, job_description: str) -> str:
    """Create an id, job description"""

    if "bucket" in job_description:
        return satellite + "_bucket_processing"

    return satellite + "_" + job_description


def raw_bucket_processing_trigger_callback(satellites_list):
    """Trigger raw bucket processing tasks. This callback is called when the buffer
    processor finishes processing one block of frames."""

    # retrieve the current scheduler instance
    scheduler = Scheduler()

    for satellite in satellites_list:
        args = [satellite]
        job_id = get_job_id(satellite, "raw_bucket_processing")
        # add a new job to the execution list
        scheduler.add_job_to_schedule(process_raw_bucket, args, job_id)


def schedule_job(job_type: str, satellite: str = None, link: str = None,
                 date: datetime = None, interval: int = None) -> None:
    """Schedule job for a specified satellite and/or link.
    Date will indicate the date and time when the task should run as datetime.
    Interval represents the time interval in minutes for adding recurring tasks."""
    scheduler = Scheduler()
    scheduler.start_scheduler()

    if job_type == "scraper" and satellite in SATELLITES:
        args = [satellite]
        job_id = get_job_id(satellite, job_type)
        scheduler.add_job_to_schedule(scrape, args, job_id, date, interval)

    elif job_type == "buffer_processing":
        # process new frames. Add the trigger callback for start the raw bucket processing tasks
        args = [False, raw_bucket_processing_trigger_callback]
        job_id = job_type
        scheduler.add_job_to_schedule(process_uplink_and_downlink, args, job_id, date, interval)

    elif job_type == "buffer_reprocessing":
        # re-process failed frames. Add the trigger callback for start the raw bucket processing tasks
        args = [True, raw_bucket_processing_trigger_callback]
        job_id = job_type
        scheduler.add_job_to_schedule(process_uplink_and_downlink, args, job_id, date, interval)

    elif job_type == "raw_bucket_processing" and satellite in SATELLITES:
        args = [satellite, link]
        job_id = get_job_id(satellite, job_type)
        scheduler.add_job_to_schedule(process_raw_bucket, args, job_id, date, interval)

    elif job_type == "reprocess_entire_raw_bucket" and satellite in SATELLITES:
        args = [satellite, link, True, False]
        job_id = get_job_id(satellite, job_type)
        scheduler.add_job_to_schedule(process_raw_bucket, args, job_id, date, interval)

    elif job_type == "reprocess_failed_raw_bucket" and satellite in SATELLITES:
        args = [satellite, link, False, True]
        job_id = get_job_id(satellite, job_type)
        scheduler.add_job_to_schedule(process_raw_bucket, args, job_id, date, interval)

    elif satellite not in SATELLITES or link not in ['uplink', 'downlink', None]:
        raise ValidationError("Select a satellite and/or link!")


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

    # Scheduler status can be running, paused, or shutdown.
    # Running: jobs are scheduled and running.
    # Paused: jobs' scheduling is paused.
    # Shutdown: job stores are cleared. Tasks can also be killed with wait=False flag.

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
                'default': ThreadPoolExecutor(10),
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
            self.scheduler.add_listener(self.exception_listener, EVENT_JOB_ERROR)

            Scheduler.__instance = self

            # TODO not very nice to start it here, but this class is a singleton and
            # in ensures the gateway is loaded only once
            XTCEParser.loadGateway()

    def get_state(self) -> str:
        """Returns the state of the scheduler: running, paused, shutdown."""
        if self.scheduler.state == STATE_STOPPED:
            return "shutdown"
        if self.scheduler.state == STATE_PAUSED:
            return "paused"
        if self.scheduler.state == STATE_RUNNING:
            return "running"

        return ""

    def exception_listener(self, event) -> None:
        """Listens to newly added jobs"""
        self.running_jobs.remove(event.job_id)
        logger.info("Terminated job: %s", event.job_id)
        logger.error(event.traceback)

    def add_job_listener(self, event) -> None:
        """Listens to newly added jobs"""
        self.pending_jobs.add(event.job_id)

    def remove_job_listener(self, event) -> None:
        """Listens to removed jobs"""
        self.pending_jobs.remove(event.job_id)

    def executed_job_listener(self, event) -> None:
        """Listens to executed jobs"""
        logger.info("Executed job: %s", event.job_id)
        self.running_jobs.remove(event.job_id)

    def submitted_job_listener(self, event) -> None:
        """Listens to submitted jobs"""
        logger.info("Started job: %s", event.job_id)
        self.running_jobs.add(event.job_id)

        if "scraper" in event.job_id:
            schedule_job("buffer_processing")

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

        if job_id not in self.running_jobs and job_id not in self.pending_jobs:
            self.scheduler.add_job(
                function,
                args=args,
                id=job_id,
                trigger=trigger,
            )
        elif job_id in self.pending_jobs:
            self.scheduler.reschedule_job(job_id, trigger=trigger)

    def start_scheduler(self) -> None:
        """Start the background scheduler"""
        if self.scheduler.state == STATE_STOPPED:
            logger.info("Scheduler started")
            self.scheduler.start()

    def pause_scheduler(self) -> None:
        """Pause the background scheduler"""
        if self.scheduler.state == STATE_RUNNING:
            logger.info("Scheduler paused")
            self.scheduler.pause()

    def resume_scheduler(self) -> None:
        """Resume the background scheduler"""
        if self.scheduler.state == STATE_PAUSED:
            logger.info("Scheduler resumed")
            self.scheduler.resume()

    def force_stop_scheduler(self) -> None:
        """Stop the scheduler. Running tasks will be killed before shutdown."""
        if self.scheduler.state != STATE_STOPPED:
            logger.info("Scheduler force shutdown")
            self.scheduler.shutdown(wait=False)

    def stop_scheduler(self) -> None:
        """Stop the scheduler. Running tasks will finish execution before shutdown."""
        if self.scheduler.state != STATE_STOPPED:
            logger.info("Scheduler shutdown")
            self.scheduler.shutdown()
