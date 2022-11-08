"""Test views html templates"""
from datetime import datetime
import json

from django.test import TestCase

from transmission.processing.bookkeep_new_data_time_range import include_timestamp_in_time_range, read_time_range_file, reset_new_data_timestamps
from transmission.processing.satellites import TIME_FORMAT
# pylint: disable=all

empty_intervals = {
                "uplink": [],
                "downlink": []
                }

interval = ["2021-12-19T02:20:13Z","2021-12-19T02:20:15Z"]

empty_ranges = {
            "delfi_pq": empty_intervals,
            "delfi_next": empty_intervals,
            "delfi_c3": empty_intervals,
            "da_vinci": empty_intervals
        }

busy_ranges = {
            "delfi_pq": {
                "uplink": interval,
                "downlink": interval
            },
            "delfi_next": {
                "uplink": interval,
                "downlink": interval
            },
            "delfi_c3": empty_intervals,
            "da_vinci": empty_intervals
        }

class TestTableViews(TestCase):

    def setUp(self):
        self.input_file = "test.json"
        self.ranges = busy_ranges

        with open(self.input_file, "w", encoding="utf-8") as file:
            file.write(json.dumps(self.ranges, indent=4))


    def tearDown(self):
        self.ranges = empty_ranges

        with open(self.input_file, "w", encoding="utf-8") as file:
            file.write(json.dumps(self.ranges, indent=4))


    def test_read_and_update(self):
        read_ranges = read_time_range_file(self.input_file)
        self.assertEqual(read_ranges, busy_ranges)
        self.assertEqual(read_ranges["da_vinci"], empty_intervals)

        timestamp = datetime.strptime("2021-11-19T02:20:13Z", TIME_FORMAT)
        include_timestamp_in_time_range("da_vinci", "uplink", timestamp, self.input_file)

        read_ranges = read_time_range_file(self.input_file)
        self.assertEqual(read_ranges["da_vinci"]["uplink"], ["2021-11-19T02:20:12Z", "2021-11-19T02:20:14Z"])


    def test_reset(self):
        read_ranges = read_time_range_file(self.input_file)
        self.assertEqual(read_ranges, busy_ranges)
        # reset delfi_pq intervals
        reset_new_data_timestamps("delfi_pq","uplink", self.input_file)
        reset_new_data_timestamps("delfi_pq","downlink", self.input_file)

        read_ranges = read_time_range_file(self.input_file)
        for sat in read_ranges:
            if sat != "delfi_pq": # check that the rest of the sats kept the same intervals
                self.assertEqual(read_ranges[sat], busy_ranges[sat])
            else:# check that delfi_pq is reset
                self.assertEqual(read_ranges["delfi_pq"], empty_intervals)


    def test_include_timestamp_in_time_range(self):
        read_ranges = read_time_range_file(self.input_file)
        self.assertEqual(read_ranges, busy_ranges)

        include_timestamp_in_time_range("delfi_pq", "uplink", "2021-12-19T02:40:15Z", self.input_file)
        read_ranges = read_time_range_file(self.input_file)
        for sat in read_ranges:
            if sat != "delfi_pq": # check that the rest of the sats kept the same intervals
                self.assertEqual(read_ranges[sat], busy_ranges[sat])
            else:# check that delfi_pq is updated
                self.assertEqual(read_ranges["delfi_pq"]["uplink"], ["2021-12-19T02:20:13Z", "2021-12-19T02:40:16Z"])
                self.assertEqual(read_ranges["delfi_pq"]["downlink"], interval)


    def test_include_timestamp_in_time_range_edge_cases(self):
        read_ranges = read_time_range_file(self.input_file)
        self.assertEqual(read_ranges, busy_ranges)
        # higher than upper bound
        include_timestamp_in_time_range("delfi_pq", "uplink", "2021-12-19T02:40:15Z", self.input_file)
        read_ranges = read_time_range_file(self.input_file)

        self.assertEqual(read_ranges["delfi_pq"]["uplink"], ["2021-12-19T02:20:13Z", "2021-12-19T02:40:16Z"])
        self.assertEqual(read_ranges["delfi_pq"]["downlink"], interval)

        # within bounds
        include_timestamp_in_time_range("delfi_pq", "uplink", "2021-12-19T02:35:15Z", self.input_file)
        read_ranges = read_time_range_file(self.input_file)

        self.assertEqual(read_ranges["delfi_pq"]["uplink"], ["2021-12-19T02:20:13Z", "2021-12-19T02:40:16Z"])

        # lower than lower bound
        include_timestamp_in_time_range("delfi_pq", "uplink", "2021-11-19T02:20:13Z", self.input_file)
        read_ranges = read_time_range_file(self.input_file)

        self.assertEqual(read_ranges["delfi_pq"]["uplink"], ["2021-11-19T02:20:12Z", "2021-12-19T02:40:16Z"])

        # no time range saved
        self.assertEqual(read_ranges["da_vinci"], empty_intervals)
        include_timestamp_in_time_range("da_vinci", "uplink", "2021-11-19T02:20:13Z", self.input_file)
        read_ranges = read_time_range_file(self.input_file)

        self.assertEqual(read_ranges["da_vinci"]["uplink"], ["2021-11-19T02:20:12Z", "2021-11-19T02:20:14Z"])
