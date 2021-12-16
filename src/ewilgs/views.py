"""API request handling. Map requests to the corresponding HTMLs."""
import json
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render
from django_pandas.io import read_frame
from .models import Uplink, Downlink
from .save_frames import register_downlink_frames

QUERY_ROW_LIMIT = 500

def home(request):
    """render index.html page"""
    ren = render(request, "ewilgs/home/index.html")
    return ren

def add_downlink_frames(request):
    """Add frames to Downlink table. The input is a list of json objects embedded in to the
    HTTP request."""
    # uncomment to add dummy data
    # with open('src/ewilgs/dummy_downlink.json', 'r') as file:
    #     dummy_data = json.load(file)
    #     register_downlink_frames(dummy_data)

    # comment the next to lines when adding dummy data
    frames_to_add = json.loads(request.body)
    register_downlink_frames(frames_to_add)

    return JsonResponse({"len": len(Downlink.objects.all())})

def filter_query(query, frames):
    """Filter a table of frames according to a given query"""

    if "id" in query and query.get("id") is not None:
        frames = frames.filter(id=query.get("id")).all()

    if "frequency" in query and query.get("frequency") is not None:
        frames = frames.filter(frequency__range=query.get("frequency")).all()

    if "frame_time" in query and query.get("frame_time") is not None:
        frames = frames.filter(frame_time__range=query.get("frame_time")).all()

    if "processed" in query and query.get("processed") is not None:
        frames = frames.filter(processed=query.get("processed")).all()

    if "radio_amateur" in query and query.get("radio_amateur") is not None:
        frames = frames.filter(radio_amateur=query.get("radio_amateur")).all()

    if "version" in query and query.get("version") is not None:
        frames = frames.filter(version=query.get("version")).all()

    if "sat" in query and query.get("sat") is not None:
        frames = frames.filter(sat=query.get("sat")).all()

    if "order_by" in query and query.get("order_by") == "oldest":
        frames = frames.order_by('-frame_time') # oldest first
    else:
        frames = frames.order_by('frame_time') # newest first

    return frames


def retrive_frames(request_body, table):
    """Query a db table and filter the results"""
#     query = {
#     "frequency" : [2000.00, 2500.00],
#     "frame_time": ["2021-12-16 13:55:14.380345+00:00", 	"2021-12-16 13:55:14.408362+00:00"],
#     # "id": 5,
#     # "radio_amateur": None,
#     # "version": None,
#     "order_by": "oldest",
# }

    if request_body == bytearray():
        uplink_frames = table.order_by('frame_time')[:QUERY_ROW_LIMIT]
        data = read_frame(uplink_frames)
        table_html = data.to_html()
        return table_html

    query = json.loads(request_body)
    # filter results
    frames = filter_query(query, table)

    # limit results
    frames = frames[:QUERY_ROW_LIMIT]
    data = read_frame(frames)
    table_html = data.to_html()

    return table_html

def get_downlink_frames(request):
    """Query downlink table (Select * LIMIT 500) if the body of the get request is empty,
    otherwise it filter the results."""

    query = request.body

    downlink_frames = Downlink.objects.all()

    # get results
    table_html = retrive_frames(query, downlink_frames)

    return HttpResponse(table_html)


def get_uplink_frames(request):
    """Query uplink table (Select * LIMIT 500) if the body of the get request is empty,
    otherwise it filter the results."""

    query = request.body
    uplink_frames = Uplink.objects.all()

    # get results
    table_html = retrive_frames(query, uplink_frames)

    return HttpResponse(table_html)

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
