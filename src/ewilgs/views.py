"""API request handling. Map requests to the corresponding HTMLs."""
import json
from django.core.paginator import Paginator
from django.http.response import JsonResponse
from django.shortcuts import render
from .models import Uplink, Downlink
from .save_frames import register_downlink_frames
from .filters import TelemetryDownlinkFilter, TelemetryUplinkFilter

QUERY_ROW_LIMIT = 100

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

    # comment the next two lines when adding dummy data
    frames_to_add = json.loads(request.body)
    register_downlink_frames(frames_to_add)

    return JsonResponse({"len": len(Downlink.objects.all())})


def paginate_telemetry_table(request, telemetry_filter, table_name):
    """Paginates a telemetry table and renders the filtering form"""

    data = telemetry_filter.qs
    paginator = Paginator(data, QUERY_ROW_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'telemetry_filter': telemetry_filter, 'page_obj': page_obj, 'table_name': table_name}
    return render(request, "ewilgs/table.html", context)


def get_downlink_table(request):
    """Queries and filters the downlink table"""
    frames = Downlink.objects.all().order_by('frame_time')
    telemetry_filter = TelemetryDownlinkFilter(request.GET, queryset=frames)
    return paginate_telemetry_table(request, telemetry_filter,  "Downlink")


def get_uplink_table(request):
    """Queries and filters the uplink table"""
    frames = Uplink.objects.all().order_by('frame_time')
    telemetry_filter = TelemetryUplinkFilter(request.GET, queryset=frames)
    return paginate_telemetry_table(request, telemetry_filter,  "Uplink")
