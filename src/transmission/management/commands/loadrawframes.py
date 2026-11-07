"""Load frames from pyTrack or DelfiGS log files directly into a satellite's raw bucket.

Examples:
  python manage.py loadrawframes delfi_pq --format pytrack "/data/x/Delfi-PQ_replayed_*.txt"
  python manage.py loadrawframes delfi_pq --format delfigs "/data/x/DelfiGS/Downlink/*.log"

Only frames whose AX.25 header matches the satellite are stored; frames from other
satellites are skipped. Frames already in the bucket are skipped as duplicates.
Frames sharing a timestamp with a different frame are shifted by 1 microsecond, since
InfluxDB would otherwise overwrite one with the other.
"""
import glob
import json
from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand, CommandError
from transmission.processing.influxdb_api import influxdb_api

# expected AX.25 header (first 16 bytes) per satellite
SATELLITE_HEADERS = {
    "delfi_pq": "8EA49EAA9C88E088988C92A0A26103F0",
    "delfi_c3": "A8989B4040400088988C9286660103F0",
}


def parse_pytrack(line: str):
    """'2022-01-14 08:47:27.912 UTC,131.694,8EA4...' -> (timestamp or None, second column, frame).
    A few lines only have 'HH:MM' (seconds dropped by the exporter); the timestamp is
    returned as None and reconstructed from the previous line by the caller."""
    time_str, second_col, frame = line.split(",")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f %Z", "%Y-%m-%d %H:%M:%S %Z"):
        try:
            return datetime.strptime(time_str, fmt).replace(tzinfo=timezone.utc), float(second_col), frame
        except ValueError:
            continue
    datetime.strptime(time_str, "%Y-%m-%d %H:%M %Z")   # still must be a valid date and minute
    return None, float(second_col), frame


def parse_delfigs(line: str):
    """'{"timestamp": "2022-01-14T10:21:42.747Z", "packet": "8EA4...", ...}' -> (timestamp, None, frame)"""
    data = json.loads(line)
    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    return timestamp, None, data["packet"]


PARSERS = {"pytrack": parse_pytrack, "delfigs": parse_delfigs}


class Command(BaseCommand):
    """Django command class"""
    help = "Load pyTrack or DelfiGS frame logs directly into a satellite's raw bucket"

    def add_arguments(self, parser):
        parser.add_argument("satellite", choices=SATELLITE_HEADERS.keys())
        parser.add_argument("patterns", nargs="+", help="file paths or quoted glob patterns")
        parser.add_argument("--format", required=True, choices=PARSERS.keys())
        parser.add_argument("--header", help="override the expected AX.25 header (hex)")
        parser.add_argument("--user", help="value for the 'user' tag (default: the format name)")
        parser.add_argument("--limit", type=int, help="stop after this many lines (for testing)")

    def handle(self, *args, **options):  # pylint: disable=too-many-locals,too-many-branches
        satellite = options["satellite"]
        header = (options["header"] or SATELLITE_HEADERS[satellite]).upper()
        parse = PARSERS[options["format"]]
        user = options["user"] or options["format"]
        limit = options["limit"]

        files = sorted({f for pattern in options["patterns"] for f in glob.glob(pattern)})
        if not files:
            raise CommandError("No files match the given paths")

        db = influxdb_api()
        total = {"lines": 0, "stored": 0, "duplicate": 0, "nudged": 0,
                 "reconstructed": 0, "other_header": 0, "bad_line": 0}
        # timestamp -> frame already used in this load; several frames can share a timestamp,
        # and in InfluxDB the second would overwrite the first
        used_timestamps = {}

        for filename in files:
            counts = dict.fromkeys(total, 0)
            previous = None   # (timestamp, second column) of the last good pyTrack line
            with open(filename, encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    if limit is not None and total["lines"] + counts["lines"] >= limit:
                        break
                    counts["lines"] += 1
                    try:
                        timestamp, second_col, frame = parse(line)
                    except (ValueError, KeyError):
                        counts["bad_line"] += 1
                        continue

                    if timestamp is None:
                        # minute-only pyTrack time: rebuild it from the previous line,
                        # using the elapsed-seconds column
                        if previous is None:
                            counts["bad_line"] += 1
                            continue
                        timestamp = previous[0] + timedelta(seconds=second_col - previous[1])
                        counts["reconstructed"] += 1
                    if second_col is not None:
                        previous = (timestamp, second_col)

                    frame = frame.strip().upper()
                    if not frame.startswith(header):
                        counts["other_header"] += 1
                        continue

                    # make the timestamp unique: shift by 1 microsecond while it is
                    # already used by a different frame
                    if timestamp in used_timestamps and used_timestamps[timestamp] != frame:
                        counts["nudged"] += 1
                        while timestamp in used_timestamps and used_timestamps[timestamp] != frame:
                            timestamp += timedelta(microseconds=1)
                    used_timestamps[timestamp] = frame

                    tlm = {"frame": frame, "user": user, "application": options["format"]}
                    if db.save_raw_frame(satellite, "downlink", timestamp, tlm):
                        counts["stored"] += 1
                    else:
                        counts["duplicate"] += 1

            for key, value in counts.items():
                total[key] += value
            self.stdout.write(f"{filename}: {counts}")
            if limit is not None and total["lines"] >= limit:
                break

        self.stdout.write(self.style.SUCCESS(f"Done: {total}"))
