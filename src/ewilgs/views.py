"""API request handling. Map requests to the corresponding HTMLs."""
from django.http.response import JsonResponse
from django_pandas.io import read_frame
from django.shortcuts import render
import pandas as pd
from django.views.generic import ListView
from django.core import serializers
from ewilgs.models import Uplink, Downlink
from ewilgs.save_frames import registerDownlinkFrames
import json
from .models import Uplink, Downlink


def home(request):
    """render index.html page"""
    ren = render(request, "home.html")
    return ren

def add_downlink_frames(request):
    # uncomment to add dummy data
    # with open('src/ewilgs/dummy_downlink.json', 'r') as file:
    #     dummy_data = json.load(file)
    #     registerDownlinkFrames(dummy_data)
    #
    # comment the next to lines at first run
    frames_to_add = json.loads(request.body)
    registerDownlinkFrames(frames_to_add)

    return JsonResponse({"len": len(Downlink.objects.all())}
                        )
def get_downlink_frames(request):
    if request.body == bytearray():
        downlink_frames = Downlink.objects.filter().all()
    else:
        query = json.loads(request.body)
        downlink_frames = Downlink.objects.filter(frequency=query.get("frequency"),
                                                    processed=query.get("processed")).all()

    df = list(downlink_frames.values_list("id", "frame_time", "frame", "frequency", "qos", "processed"))
    # print(df)
    return render(request, 'ewilgs/downlink.html', {"df": df})


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
