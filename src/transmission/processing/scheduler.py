"""Scheduler for planning telemetry scrapes and frame processing"""
from apscheduler.schedulers.background import BackgroundScheduler
from transmission.processing.process_raw_bucket import process_raw_bucket
from transmission.processing.telemetry_scraper import scrape
from transmission.processing.save_raw_data import process_uplink_and_downlink


scheduler = BackgroundScheduler()

def add_scraper_job(satellite, trigger=None, minutes=None):
    """Add a satnogs scraper job"""
    scheduler.add_job(
            scrape,
            args=[satellite],
            trigger=trigger,
            minutes=minutes,
            id=satellite + '_scraper_job',
            max_instances=1
        )


def start():
    """Start the background scheduler"""
    # Trigger:
        # date: use when you want to run the job just once at a certain point of time
        # interval: use when you want to run the job at fixed intervals of time
        # cron: use when you want to run the job periodically at certain time(s) of day

    scheduler.add_job(
            process_uplink_and_downlink,
            trigger='interval',
            minutes= 1,
            id='frame_processor_postgres',
            max_instances=1
        )

    add_scraper_job("delfi_pq", trigger="interval", minutes=60*12)
    # add_scraper_job("delfi_next", trigger="interval", minutes=60*12)
    # add_scraper_job("delfi_c3", trigger="interval", minutes=60*12)
    # add_scraper_job("da_vinci", trigger="interval", minutes=60*12)


    scheduler.add_job(
        process_raw_bucket,
        args=["delfi_pq","downlink"],
        trigger='interval',
        minutes= 1,
        id='delfi_pq_frame_processor_influxdb',
        max_instances=1
        )


    scheduler.start()


def stop():
    """Stop the scheduler"""
    scheduler.shutdown()
