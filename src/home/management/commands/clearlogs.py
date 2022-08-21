"""Custom command to clear django log files
Run with 'python manage.py clearlogs' """
import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Django command class"""

    def handle(self, *args, **options):
        """Clear log files"""
        logs_dir = 'logs'

        for file in os.listdir(logs_dir):
            log_file = os.path.join(logs_dir, file)
            if os.path.isfile(log_file):
                # clear the data in the log file
                with open(log_file, 'w', encoding='utf-8') as _ :
                    pass
