"""Scheduler for planning telemetry scrapes and frame processing"""
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ADDED, EVENT_JOB_REMOVED,\
EVENT_JOB_EXECUTED,EVENT_JOB_SUBMITTED
from transmission.processing.process_raw_bucket import process_raw_bucket
from transmission.processing.telemetry_scraper import scrape
from transmission.processing.save_raw_data import process_uplink_and_downlink
from django_logger import logger

# Trigger:
    # date: use when you want to run the job just once at a certain point of time
    # interval: use when you want to run the job at fixed intervals of time
    # cron: use when you want to run the job periodically at certain time(s) of day

# Scheduler workflow: add job -> remove job -> submit job -> execute job

class Singleton(type):
    """Singleton class"""
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ProcessingScheduler(metaclass=Singleton):
    """Scheduler handling frame processing jobs. Employs the singleton design pattern."""
    __instance = None

    @staticmethod
    def get_instance():
        """ Returns class instance"""
        return ProcessingScheduler.__instance

    def __init__(self) -> None:
        if ProcessingScheduler.__instance is not None:
            logger.info("Scheduler already instantiated")
        else:
            executors = {
                'default': ThreadPoolExecutor(1),
                # 'processpool': ProcessPoolExecutor(0)
            }
            job_defaults = {
                'coalesce': False,
                'max_instances': 1
            }

            self.running_jobs = set()
            self.pending_jobs = set()

            self.scheduler = BackgroundScheduler(job_defaults=job_defaults, executors=executors)

            self.scheduler.add_listener(self.submitted_job_listener, EVENT_JOB_SUBMITTED)
            self.scheduler.add_listener(self.executed_job_listener, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self.add_job_listener, EVENT_JOB_ADDED)
            self.scheduler.add_listener(self.remove_job_listener, EVENT_JOB_REMOVED)

            ProcessingScheduler.__instance = self

            self.start_scheduler()


    def add_job_listener(self, event):
        """Listens to newly added jobs"""
        logger.info("Scheduler added job: %s", event.job_id)
        self.pending_jobs.add(event.job_id)


    def remove_job_listener(self, event):
        """Listens to removed jobs"""
        logger.info("Scheduler removed job: %s", event.job_id)
        self.pending_jobs.remove(event.job_id)


    def executed_job_listener(self, event):
        """Listens to executed jobs"""
        logger.info("Scheduler executed job: %s", event.job_id)
        self.running_jobs.remove(event.job_id)


    def submitted_job_listener(self, event):
        """Listens to submitted jobs"""
        self.running_jobs.add(event.job_id)
        logger.info("Scheduler submitted job: %s", event.job_id)


    def get_pending_jobs(self) -> list:
        """Get the ids of the currently scheduled jobs."""
        return self.pending_jobs

    def get_running_jobs(self) -> list:
        """Get the ids of the currently running jobs."""
        return self.running_jobs

    @staticmethod
    def get_job_id(satellite: str, job_description: str, link: str=None) -> str:
        """Create an id, job description"""
        if link is None:

            return satellite + "_" + job_description

        return satellite + "_" + link + "_" + job_description


    def schedule_job(self, satellite: str, job_type: str, link: str) -> None:
        """Schedule job"""
        if job_type == "scraper":
            args = [satellite]
            job_id = self.get_job_id(satellite, job_type)
            self.add_job_to_schedule(scrape, args, job_id)

        elif job_type == "buffer_processing":
            args = []
            job_id = job_type
            self.add_job_to_schedule(process_uplink_and_downlink, args, job_id)

        elif job_type == "raw_bucket_processing":
            args = [satellite, link]
            job_id = self.get_job_id(satellite, job_type, link)
            self.add_job_to_schedule(process_raw_bucket, args, job_id)


    def add_job_to_schedule(self, function: Callable, args:list, job_id:str) -> None:
        """Add a job to the schedule if not already scheduled."""
        if job_id not in self.running_jobs and job_id not in self.pending_jobs:
            self.scheduler.add_job(
                    function,
                    args=args,
                    id=job_id,
                )


    def start_scheduler(self) -> None:
        """Start the background scheduler"""
        logger.info("Scheduler started")
        self.scheduler.start()


    def stop_scheduler(self) -> None:
        """Stop the scheduler"""
        logger.info("Scheduler shutdown")
        self.scheduler.shutdown()
