"""API request handling. Map requests to the corresponding HTMLs."""
from datetime import datetime, timedelta
import json
import os
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.http.response import JsonResponse
from django.shortcuts import render
from pycrowdsec.client import StreamClient
from skyfield.api import load, EarthSatellite, wgs84, Topos
from satellite_tle import fetch_tle_from_celestrak
from transmission.processing.satellites import SATELLITES, TIME_FORMAT

#pylint: disable=W0718
def get_tle(norad_id: str):
    """Retrieve satellite TLE by noradID and store it in a json.
     If the stored TLE is older than 6 hours a fresh one is requested from CelesTrak."""

    if os.path.exists(os.getcwd() + "/home/temp/tle.json"):
        with open(os.getcwd() + "/home/temp/tle.json", "r", encoding="utf8") as file:
            tles = json.load(file)
    else:
        tles = {}

    now = datetime.utcnow()

    if norad_id in tles and "timestamp" in tles[norad_id]:
        last_timestamp = datetime.strptime(tles[norad_id]["timestamp"], TIME_FORMAT)
        if (now - last_timestamp).seconds < 6 * 3600:  # update every 6 hours
            return tles[norad_id]['tle']

    try:
        fresh_tle = fetch_tle_from_celestrak(norad_id)
        tles[norad_id] = {}
        tles[norad_id]["tle"] = fresh_tle
        tles[norad_id]["timestamp"] = now.strftime(TIME_FORMAT)

        with open(os.getcwd() + "/home/temp/tle.json", "w", encoding="utf8") as file:
            file.write(json.dumps(tles, indent=4, cls=DjangoJSONEncoder))
            return tles[norad_id]['tle']

    except Exception as _:
        pass

    return None


def get_satellite_location_now(norad_id: str) -> dict:
    """Return latitude and longitude of the satellite at the present time based on TLE. """
    tle = get_tle(norad_id)

    if tle is None:
        return {"satellite": None, "latitude": None, "longitude": None, "sunlit": None}

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

    return {"satellite": str(tle[0]), "latitude": lat_deg, "longitude": lon_deg, "sunlit": int(sunlit)}


def get_next_pass_over_delft(request, norad_id: str):
    """Calculate next passes over Delft in the following 24 hours."""
    tle = get_tle(norad_id)
    time_scale = load.timescale()
    satellite = EarthSatellite(tle[1], tle[2], tle[0], time_scale)

    # Location of Delft (EWI)
    delft = Topos("52.0022 N", "4.3736 E")

    # Calculate the next pass over Delft within the next 24 hours
    timestamps, events = satellite.find_events(delft, time_scale.now(), time_scale.now() + timedelta(hours=24))

    pass_events = []
    min_events = min(len(timestamps[events == 0]), len(timestamps[events == 1]), len(timestamps[events == 2]))

    for i in range(min_events):
        rise_time = timestamps[events == 0][i].utc_datetime().strftime(TIME_FORMAT)
        peak_time = timestamps[events == 1][i].utc_datetime().strftime(TIME_FORMAT)
        set_time = timestamps[events == 2][i].utc_datetime().strftime(TIME_FORMAT)
        pass_events.append({"rise_time": rise_time, "peak_time": peak_time, "set_time": set_time})

    return JsonResponse({"satellite": str(tle[0]), "passes": pass_events})


def get_satellite_location_now_api(request, norad_id):
    """API exposed method to find satellite location."""
    if norad_id == "all":
        sat_list = []
        for _, info in SATELLITES.items():
            if info["status"] != "Decayed":
                sat_list.append(get_satellite_location_now(info["norad_id"]))

        res = {"satellites": sat_list}
        return JsonResponse(res)

    location = get_satellite_location_now(norad_id)
    return JsonResponse(location)


def _get_satellites_status():
    """Method to find satellite status."""
    sats_status = {}
    for sat, info in SATELLITES.items():
        sats_status[str(sat + "_status")] = info["status"]

    return sats_status


def get_satellites_status(request):
    """API exposed method to find satellite status."""
    sats_status = _get_satellites_status()
    return JsonResponse(sats_status)


def home(request):
    """Render index.html page"""
    context = _get_satellites_status()
    return render(request, "home/index.html", context)


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
