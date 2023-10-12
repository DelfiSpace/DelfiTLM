"""Custom command for populating the GS frame buffer.
Run with 'python manage.py addgsdata' """
import json
import os
from django.core.management.base import BaseCommand

from transmission.models import Downlink, Uplink
from members.models import Member
from django.core.management import call_command
# pylint: disable=all
class Command(BaseCommand):
    """Django command class"""

    def handle(self, *args, **options):
        # check if admin exists, if not create it
        if len(Member.objects.filter(username="admin")) == 0:
            call_command('initadmin')
        # Get a list of all files and directories in the specified folder
        folder_path = "delfipq/delfipq3/"
        files = os.listdir(folder_path)

        # Filter out only the files from the list
        file_names = [os.path.join(folder_path, file) for file in files if os.path.isfile(os.path.join(folder_path, file))]

        for input_file in file_names:

            json_objects = []
            try:
                # Open the log file
                with open(input_file, 'r', encoding='utf-8') as file:
                    # Read the file line by line
                    for line in file:
                        # Parse each line as a JSON object and add it to the list
                        try:
                            json_object = json.loads(line)
                            json_objects.append(json_object)
                        except json.JSONDecodeError as e:
                            print(f"Error parsing line: {line}\n{e}")
            except FileNotFoundError:
                print("File not found.")
            except PermissionError:
                print("Permission error occurred. Check your permissions.")
            except Exception as e:
                print(f"An error occurred: {e}")


            if "downlink" in input_file:

                    for frame in json_objects:
                        frame_entry = Downlink()
                        frame_entry.observer = Member.objects.all().filter(username="admin")[0]
                        frame_entry.frame = frame["packet"]
                        frame_entry.timestamp = frame["timestamp"]
                        frame_entry.frequency = frame["frequency"]
                        frame_entry.save()
            else:
                    for frame in json_objects:
                        frame_entry = Uplink()
                        frame_entry.operator = Member.objects.all().filter(username="admin")[0]
                        frame_entry.frame = frame["packet"]
                        frame_entry.timestamp = frame["timestamp"]
                        frame_entry.frequency = frame["frequency"]
                        frame_entry.save()

