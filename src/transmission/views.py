"""API request handling. Map requests to the corresponding HTMLs."""
import json
from json.decoder import JSONDecodeError
from django.core.paginator import Paginator
from django.forms import ValidationError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest
from django.http import HttpResponseBadRequest
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.decorators import permission_classes
from members.models import APIKey
from .models import Uplink, Downlink, TLE
from .filters import TelemetryDownlinkFilter, TelemetryUplinkFilter, TLEFilter
from .save_data import parse_submitted_frame, process_frames, store_frame


QUERY_ROW_LIMIT = 100

@permission_classes([HasAPIKey,])
def submit_frame(request): #pylint:disable=R0911
    """Add frames to Uplink/Downlink table. The input is a list of json objects embedded in to the
    HTTP request."""

    #  TO DO: Add uplink/downlink identifier in the http request

    if request.method == 'POST':
        try:
            # retrieve the authorization header (if present, empty otherwise)
            key = request.META.get("HTTP_AUTHORIZATION",'')
            # retrieve the user agent (if present, empty otherwise)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            link = 'downlink'

            if 'HTTP_FRAME_LINK' in request.META and \
                request.META.get('HTTP_FRAME_LINK', '') is not None:

                link = request.META.get('HTTP_FRAME_LINK', '')

                if link not in ["uplink", "downlink"]:
                    raise BadRequest("HTTP_FRAME_LINK can be either 'uplink' or 'downlink'" )

            # search for the user name matching the API key
            api_key_name = APIKey.objects.get_from_key(key)
            # retrieve the JSON frame just submitted
            frame_to_add = json.loads(request.body)
            # add the frame to the database
            store_frame(frame_to_add, link, username=api_key_name,  application=user_agent)
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
            print(message_text)
            return JsonResponse({"result": "failure", "message": message_text}, status=500)

    # POST is the only supported method, return error
    return JsonResponse({"result": "failure", "message": "Method not allowed"}, status=405)


def add_dummy_downlink_frames(request):
    """Add frames to Downlink table. The input is a list of json objects embedded in to the
    HTTP request."""

    with open("transmission/dummy_downlink.json", 'r', encoding="utf-8") as file:
        dummy_data = json.load(file)
        for frame in dummy_data["frames"]:
            frame_entry = Downlink()
            frame_entry = parse_submitted_frame(frame, frame_entry)
            frame_entry.save()

    return JsonResponse({"len": len(Downlink.objects.all())})


@login_required(login_url='/login')
def delete_processed_frames(request, link):
    """Remove the processed frames that are already stored in influxdb"""
    user = request.user
    if link == "uplink" and  user.has_perm("transmission.delete_uplink"):
        removed_data_len = len(Uplink.objects.all().filter(processed=True))
        Uplink.objects.all().filter(processed=True).delete()
        messages.info(request, f"{removed_data_len} processed {link} frames were removed.")

    elif link == "downlink" and user.has_perm("transmission.delete_downlink"):
        removed_data_len = len(Downlink.objects.all().filter(processed=True))
        Downlink.objects.all().filter(processed=True).delete()
        messages.info(request, f"{removed_data_len} processed {link} frames were removed.")
    else:
        messages.error(request, "Operation not allowed.")

    return redirect('get_frames_table', link)


@login_required(login_url='/login')
def process(request, link):
    """Process frames that are not already stored in influxdb"""

    user = request.user
    if link == "uplink" and user.has_perm("transmission.view_uplink"):
        uplink_frames = Uplink.objects.all().filter(processed=False)
        processed_frame_count = process_frames(uplink_frames, link)
        messages.info(request, f"{processed_frame_count} {link} frames were processed.")

    elif link == "downlink" and user.has_perm("transmission.view_downlink"):
        downlink_frames = Downlink.objects.all().filter(processed=False)
        processed_frame_count = process_frames(downlink_frames, link)
        messages.info(request, f"{processed_frame_count} {link} frames were processed.")
    else:
        messages.error(request, "Operation not allowed.")

    return redirect('get_frames_table', link)


def paginate_telemetry_table(request, telemetry_filter, table_name):
    """Paginates a telemetry table and renders the filtering form"""

    data = telemetry_filter.qs
    paginator = Paginator(data, QUERY_ROW_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'telemetry_filter': telemetry_filter, 'page_obj': page_obj, 'table_name': table_name}
    return render(request, "transmission/table.html", context)


def get_frames_table(request, link):
    """Queries and filters the uplink/downlink table"""
    if link == "downlink" and request.user.has_perm('transmission.view_downlink'):
        frames = Downlink.objects.all().order_by('timestamp')
        telemetry_filter = TelemetryDownlinkFilter(request.GET, queryset=frames)
        return paginate_telemetry_table(request, telemetry_filter, "Downlink")

    if link == "uplink" and request.user.has_perm('transmission.uplink_downlink'):
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
