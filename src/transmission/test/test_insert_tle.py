from django.test import TestCase
from transmission.models import TLE, Satellite
from transmission.processing.save_raw_data import save_tle
import datetime as dt
from datetime import timezone

# pylint: disable=all

class TestTLE(TestCase):

    def test_insert_tle(self):
        tle= """ISS (ZARYA)
1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""
        new_sat = Satellite()
        new_sat.sat = "ISS (ZARYA)"
        new_sat.norad_id = 25544
        new_sat.save()

        save_tle(tle)
        tle_instance = TLE.objects.all()[0]
        self.assertEqual(tle_instance.sat, new_sat)
        self.assertEqual(tle_instance.tle, tle)
        self.assertEqual(tle_instance.valid_from, dt.datetime(2008, 9, 20, 12, 25, 40, 104187, tzinfo=timezone.utc))
        self.assertEqual(len(TLE.objects.all()), 1)
