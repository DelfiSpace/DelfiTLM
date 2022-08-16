"""Apps config file"""

from django.apps import AppConfig
import os

# pylint: disable=all
class TransmissionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transmission'

    def ready(self):
        # start the scheduler only in production
        DEBUG = bool(int(os.environ.get('DEBUG', 1)))
        if not DEBUG:
            import transmission.scheduler as scheduler
            scheduler.start()
            print("Scheduler started")
