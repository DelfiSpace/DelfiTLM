"""API request handling. Map requests to the corresponding HTMLs."""
from django.shortcuts import render
import pandas as pd
from django.views.generic import ListView
from django.core import serializers
from ewilgs.models import Uplink, Downlink
def home(request):
    """render index.html page"""
    ren = render(request, "ewilgs/home/index.html")
    return ren

def DownlinkView(request):
    ob = Downlink.objects.all()
    df = list(ob.values_list("id", "received_at", "data", "frequency", "processed"))
    return render(request, 'ewilgs/Downlink/index.html', {"df": df})
