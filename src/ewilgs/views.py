"""API request handling. Map requests to the corresponding HTMLs."""
from django.shortcuts import render
import pandas as pd
from django.views.generic import ListView
from django.core import serializers
from ewilgs.models import Uplink, Downlink
from ewilgs.save_frames import registerDownlinkFrames
import json

def home(request):
    """render index.html page"""
    ren = render(request, "ewilgs/home/index.html")
    return ren

def addDownlinkFrames(request):
    frames_to_add = json.loads(request.body)
    registerDownlinkFrames(frames_to_add)

def getDownlinkFrames(request, input):
    query = json.loads(input)
    downlink_frames = Downlink.objects.filter(frequency=query.get("frequency"),
                                                processed=query.get("processed")).all()

    df = list(downlink_frames.values_list("id", "received_at", "data", "frequency", "processed"))
    return render(request, 'ewilgs/Downlink/index.html', {"df": df})

