"""Load frames from pyTrack, DelfiGS or SatNOGS files directly into a satellite's raw bucket.

Examples:
  python manage.py loadrawframes delfi_pq --format pytrack "/data/x/Delfi-PQ_replayed_*.txt"
  python manage.py loadrawframes delfi_pq --format delfigs "/data/x/DelfiGS/Downlink/*.log" --window 1
  python manage.py loadrawframes delfi_pq --format satnogs "/data/x/delfi-pq_satnogs_dump.txt" --window 1

Only frames whose AX.25 header matches the satellite are stored; frames from other
satellites are skipped. Frames already in the bucket are skipped as duplicates.
Use --window to widen the duplicate check when another logger stamped the same frames
slightly differently (pass logs, DelfiGS and SatNOGS: use --window 1).
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


def parse_pytrack(record: str):
    """'2022-01-14 08:47:27.912 UTC,131.694,8EA4...' -> (timestamp or None, second column, frame, tags).
    A few lines only have 'HH:MM' (seconds dropped by the exporter); the timestamp is
    returned as None and reconstructed from the previous line by the caller."""
    time_str, second_col, frame = record.split(",")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f %Z", "%Y-%m-%d %H:%M:%S %Z"):
        try:
            timestamp = datetime.strptime(time_str, fmt).replace(tzinfo=timezone.utc)
            return timestamp, float(second_col), frame, None
        except ValueError:
            continue
    datetime.strptime(time_str, "%Y-%m-%d %H:%M %Z")   # still must be a valid date and minute
    return None, float(second_col), frame, None


def parse_delfigs(record: str):
    """'{"timestamp": "2022-01-14T10:21:42.747Z", "packet": "8EA4...", ...}' -> (timestamp, None, frame, tags)"""
    data = json.loads(record)
    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    return timestamp, None, data["packet"], None


def parse_satnogs(record: dict):
    """{"timestamp": "2022-01-14T02:08:02Z", "frame": "8EA4...", "observer": ..., "app_source": ...}
    -> (timestamp, None, frame, tags with the receiving station)"""
    timestamp = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
    tags = {"user": record.get("observer") or "satnogs", "application": record.get("app_source") or "satnogs"}
    return timestamp, None, record["frame"], tags


PARSERS = {"pytrack": parse_pytrack, "delfigs": parse_delfigs, "satnogs": parse_satnogs}


def read_records(filename: str, file_format: str):
    """Yield the records of a file: JSON list items for SatNOGS dumps, non-empty lines otherwise."""
    with open(filename, encoding="utf-8") as file:
        if file_format == "satnogs":
            yield from json.load(file)
        else:
            for line in file:
                line = line.strip()
                if line:
                    yield line


class Command(BaseCommand):
    """Django command class"""
    help = "Load pyTrack, DelfiGS or SatNOGS frame files directly into a satellite's raw bucket"

    def add_arguments(self, parser):
        parser.add_argument("satellite", choices=SATELLITE_HEADERS.keys())
        parser.add_argument("patterns", nargs="+", help="file paths or quoted glob patterns")
        parser.add_argument("--format", required=True, choices=PARSERS.keys())
        parser.add_argument("--header", help="override the expected AX.25 header (hex)")
        parser.add_argument("--user", help="value for the 'user' tag (default: the format name, "
                                           "or the receiving station for SatNOGS)")
        parser.add_argument("--limit", type=int, help="stop after this many records (for testing)")
        parser.add_argument("--window", type=float, default=0.1,
                            help="seconds within which the same frame counts as a duplicate (default 0.1)")

    def handle(self, *args, **options):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        satellite = options["satellite"]
        file_format = options["format"]
        header = (options["header"] or SATELLITE_HEADERS[satellite]).upper()
        parse = PARSERS[file_format]
        default_tags = {"user": options["user"] or file_format, "application": file_format}
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
            for record in read_records(filename, file_format):
                if limit is not None and total["lines"] + counts["lines"] >= limit:
                    break
                counts["lines"] += 1
                try:
                    timestamp, second_col, frame, tags = parse(record)
                except (ValueError, KeyError, TypeError, AttributeError):
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

                if tags is None or options["user"]:
                    tags = default_tags
                tlm = {"frame": frame, **tags}
                if db.save_raw_frame(satellite, "downlink", timestamp, tlm, window=options["window"]):
                    counts["stored"] += 1
                else:
                    counts["duplicate"] += 1

            for key, value in counts.items():
                total[key] += value
            self.stdout.write(f"{filename}: {counts}")
            if limit is not None and total["lines"] >= limit:
                break

        self.stdout.write(self.style.SUCCESS(f"Done: {total}"))
