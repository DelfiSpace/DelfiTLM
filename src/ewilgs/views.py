"""API request handling. Map requests to the corresponding HTMLs."""
import json
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest
from django.http.response import JsonResponse
from django.shortcuts import render
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.decorators import permission_classes
from members.models import APIKey
from .models import Uplink, Downlink
from .save_frames import register_downlink_frames, add_frame
from .filters import TelemetryDownlinkFilter, TelemetryUplinkFilter


QUERY_ROW_LIMIT = 100

@permission_classes([HasAPIKey,])
def submit_frame(request):
    """Add frames to Downlink table. The input is a list of json objects embedded in to the
    HTTP request."""

    if request.method == 'POST':

        key = request.META["HTTP_AUTHORIZATION"]

        try: # try to find key match

            api_key_name = APIKey.objects.get_from_key(key)
            frame_to_add = json.loads(request.body)
            add_frame(frame_to_add, username=api_key_name)
            return JsonResponse({"frame_added": frame_to_add['frame']})

        except:  #pylint:disable=W0702
            # no match, no access
            return HttpResponseBadRequest("Unauthorized")

    return JsonResponse({"frame_added": {}})



def add_dummy_downlink_frames(request):
    """Add frames to Downlink table. The input is a list of json objects embedded in to the
    HTTP request."""

    with open('src/ewilgs/dummy_downlink.json', 'r', encoding="utf-8") as file:
        dummy_data = json.load(file)
        register_downlink_frames(dummy_data)

    return JsonResponse({"len": len(Downlink.objects.all())})


def home(request):
    """render index.html page"""
    ren = render(request, "ewilgs/home/index.html")
    return ren


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
