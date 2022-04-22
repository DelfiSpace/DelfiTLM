"""API request handling. Map requests to the corresponding HTMLs."""
import json
from json.decoder import JSONDecodeError
from django.core.paginator import Paginator
from django.forms import ValidationError
from django.core.exceptions import BadRequest
from django.http.response import JsonResponse
from django.shortcuts import render
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.decorators import permission_classes
from members.models import APIKey
from .models import Uplink, Downlink, TLE
from .filters import TelemetryDownlinkFilter, TelemetryUplinkFilter, TLEFilter
from .save_data import parse_frame, add_frame


QUERY_ROW_LIMIT = 100

@permission_classes([HasAPIKey,])
def submit_frame(request):
    """Add frames to Uplink/Downlink table. The input is a list of json objects embedded in to the
    HTTP request."""

    #  TO DO: Add uplink/downlink identifier in the http request

    if request.method == 'POST':
        try:
            # retrieve the authorization header (if present, empty otherwise)
            key = request.META.get("HTTP_AUTHORIZATION",'')
            # retrieve the user agent (if present, empty otherwise)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            qualifier = 'downlink'

            if 'HTTP_FRAME_TYPE' in request.META and request.META.get('HTTP_FRAME_TYPE', '') is not None:
                qualifier = request.META.get('HTTP_FRAME_TYPE', '')

            # search for the user name matching the API key
            api_key_name = APIKey.objects.get_from_key(key)
            # retrieve the JSON frame just submitted
            frame_to_add = json.loads(request.body)
            # add the frame to the database
            add_frame(frame_to_add, qualifier=qualifier, username=api_key_name,  application=user_agent)
            return JsonResponse({"result": "success", "message": ""}, status=201)

        except APIKey.DoesNotExist as e: #pylint:disable=C0103
            # catch a wrong API key
            return JsonResponse({"result": "failure", "message": str(e)}, status=401)

        except BadRequest as e: #pylint:disable=C0103, W0612
            # catch submission without right permission
            return JsonResponse({"result": "failure", "message": str(e)}, status=401)

        except JSONDecodeError as e: #pylint:disable=C0103, W0612
            # catch an error in the JSON request
            message_text = "Invalid JSON structure"
            return JsonResponse({"result": "failure", "message": message_text}, status=400)

        except ValidationError as e: #pylint:disable=C0103, W0612
            # catch an error in the frame fromatting
            return JsonResponse({"result": "failure", "message": str(e)}, status=400)

        except Exception as e:  #pylint:disable=C0103, W0703
            # catch other exceptions
            message_text = type(e).__qualname__+": "+str(e)
            return JsonResponse({"result": "failure", "message": message_text}, status=500)

    # POST is the only supported method, return error
    return JsonResponse({"result": "failure", "message": "Method not allowed"}, status=405)


def add_dummy_downlink_frames(request):
    """Add frames to Downlink table. The input is a list of json objects embedded in to the
    HTTP request."""

    with open("src/transmission/dummy_downlink.json", 'r', encoding="utf-8") as file:
        dummy_data = json.load(file)
        for frame in dummy_data["frames"]:
            frame_entry = Downlink()
            frame_entry = parse_frame(frame, frame_entry)
            frame_entry.save()

    return JsonResponse({"len": len(Downlink.objects.all())})


def home(request):
    """render index.html page"""
    ren = render(request, "transmission/home/index.html")
    return ren


def paginate_telemetry_table(request, telemetry_filter, table_name):
    """Paginates a telemetry table and renders the filtering form"""

    data = telemetry_filter.qs
    paginator = Paginator(data, QUERY_ROW_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'telemetry_filter': telemetry_filter, 'page_obj': page_obj, 'table_name': table_name}
    return render(request, "transmission/table.html", context)


def get_downlink_table(request):
    """Queries and filters the downlink table"""
    frames = Downlink.objects.all().order_by('timestamp')
    telemetry_filter = TelemetryDownlinkFilter(request.GET, queryset=frames)
    return paginate_telemetry_table(request, telemetry_filter, "Downlink")


def get_uplink_table(request):
    """Queries and filters the uplink table"""
    if request.user.has_perm('transmission.view_uplink'):
        frames = Uplink.objects.all().order_by('timestamp')
        telemetry_filter = TelemetryUplinkFilter(request.GET, queryset=frames)
        return paginate_telemetry_table(request, telemetry_filter, "Uplink")

    return HttpResponseBadRequest()

def get_tle_table(request):
    """Queries and filters the TLEs table"""
    frames = TLE.objects.all().order_by('valid_from')
    tle_filter = TLEFilter(request.GET, queryset=frames)

    data = tle_filter.qs
    paginator = Paginator(data, QUERY_ROW_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'telemetry_filter': tle_filter, 'page_obj': page_obj, 'table_name': 'TLE'}
    return render(request, "transmission/tle_table.html", context)
