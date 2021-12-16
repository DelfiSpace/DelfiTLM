"""API request handling. Map requests to the corresponding HTMLs."""
import json
from django.http.response import JsonResponse
from django.shortcuts import render
from django_pandas.io import read_frame
from ewilgs.models import Uplink, Downlink
from ewilgs.save_frames import register_downlink_frames
from .models import Uplink, Downlink

def home(request):
    """render index.html page"""
    ren = render(request, "home.html")
    return ren

def add_downlink_frames(request):
    """Add frames to Downlink table. The input is a list of json objects embedded in to the
    HTTP request."""
    # uncomment to add dummy data
    # with open('src/ewilgs/dummy_downlink.json', 'r') as file:
    #     dummy_data = json.load(file)
    #     register_downlink_frames(dummy_data)
    #
    # comment the next to lines at first run
    frames_to_add = json.loads(request.body)
    register_downlink_frames(frames_to_add)

    return JsonResponse({"len": len(Downlink.objects.all())})

def get_downlink_frames(request):
    """Query uplink table (Select *) if the body of the get request is empty,
    otherwise it filter the results."""

    if request.body == bytearray():
        downlink_frames = Downlink.objects.filter().all()
    else:
        query = json.loads(request.body)
        downlink_frames = Downlink.objects.filter(frequency=query.get("frequency"),
                                                    processed=query.get("processed")).all()

    data = list(downlink_frames)
    return render(request, 'ewilgs/downlink.html', {"data": data})


def query_uplink_downlink(request):
    """Query uplink and downlink table (Select *) and return the results"""
    uplink = Uplink.objects.all()
    df_uplink = read_frame(uplink)
    uplink_html = df_uplink.to_html()

    downlink = Downlink.objects.all()
    df_downlink = read_frame(downlink)
    downlink_html = df_downlink.to_html()

    ren_uplink = render(request, "ewilgs/data/index.html", {'uplink_html': uplink_html})
    ren_downlink = render(request, "ewilgs/data/index.html", {'downlink_html': downlink_html})

    return ren_uplink, ren_downlink
