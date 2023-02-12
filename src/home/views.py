"""API request handling. Map requests to the corresponding HTMLs."""
from datetime import datetime
import json
import os
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.http.response import JsonResponse
from django.shortcuts import render
from pycrowdsec.client import StreamClient
from skyfield.api import load, EarthSatellite, wgs84
from satellite_tle import fetch_tle_from_celestrak
from transmission.processing.satellites import SATELLITES, TIME_FORMAT


def get_tle(norad_id: str):
    """Retrieve satellite TLE by noradID and store it in a json.
     If the stored TLE is older than 6 hours a fresh one is requested from CelesTrak."""

    with open(os.getcwd() + "/home/tle.json", "r", encoding="utf8") as file:
        tles = json.load(file)

    if norad_id not in tles:
        return None

    now = datetime.utcnow()

    if "timestamp" in tles[norad_id]:
        last_timestamp = datetime.strptime(tles[norad_id]["timestamp"], TIME_FORMAT)
        if (now - last_timestamp).seconds < 6 * 3600:  # update every 6 hours
            return tles[norad_id]['tle']

    fresh_tle = fetch_tle_from_celestrak(norad_id)
    tles[norad_id]["timestamp"] = now.strftime(TIME_FORMAT)
    tles[norad_id]["tle"] = fresh_tle

    with open(os.getcwd() + "/home/tle.json", "w", encoding="utf8") as file:
        file.write(json.dumps(tles, indent=4, cls=DjangoJSONEncoder))

    return tles[norad_id]['tle']


def get_satellite_location_now(norad_id: str) -> dict:
    """Return latitude and longitude of the satellite at the present time based on TLE. """

    tle = get_tle(norad_id)
    time_scale = load.timescale()
    time = time_scale.now()

    satellite = EarthSatellite(tle[1], tle[2], tle[0], time_scale)
    geocentric = satellite.at(time)

    # calculate coordinates
    lat, lon = wgs84.latlon_of(geocentric)
    lat_deg = lat.degrees
    lon_deg = lon.degrees

    # check if satellite in eclipse
    eph = load('de421.bsp')
    sunlit = satellite.at(time).is_sunlit(eph)

    return {"latitude": lat_deg, "longitude": lon_deg, "sunlit": int(sunlit)}


def get_satellite_location_now_api(request, norad_id):
    """API exposed method to find satellite location."""
    location = get_satellite_location_now(norad_id)
    return JsonResponse(location)


def home(request):
    """Render index.html page"""

    res = get_satellite_location_now(SATELLITES["delfi_pq"])

    return render(request, "home/index.html", res)


def ban_view(request):
    """Ban request"""
    raise PermissionDenied


def test_view(request):
    """Test connection to crowdsec"""
    client = StreamClient(
        api_key=os.environ.get('CROWDSEC_LAPI'),
        lapi_url=os.environ.get('CROWDSEC_URL')
    )

    client.run()
    assert client.get_action_for("127.0.0.1") != "ban"

    return render(request, "home/index.html")
