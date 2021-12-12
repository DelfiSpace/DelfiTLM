"""API request handling. Map requests to the corresponding HTMLs."""
from django_pandas.io import read_frame
from django.shortcuts import render
from .models import Uplink, Downlink

def home(request):
    """render index.html page"""
    ren = render(request, "ewilgs/home/index.html")
    return ren

def query_uplink_downlink(request):
    """Query uplink and downlink table (Select *) and return the results"""
    uplink = Uplink.objects.all()
    df_uplink = read_frame(uplink)
    uplink_html = df_uplink.to_html()

    downlink = Downlink.objects.all()
    df_downlink = read_frame(downlink)
    downlink_html = df_downlink.to_html()

    ren_uplink = render(request, "ewilgs/Data/index.html", {'uplink_html': uplink_html})
    ren_downlink = render(request, "ewilgs/Data/index.html", {'downlink_html': downlink_html})

    return ren_uplink, ren_downlink
