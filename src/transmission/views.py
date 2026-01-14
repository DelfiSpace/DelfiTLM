"""API request handling. Map requests to the corresponding HTMLs."""
from datetime import datetime
from http import HTTPStatus
import json
from json.decoder import JSONDecodeError
from django.core.paginator import Paginator
from django.forms import ValidationError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, PermissionDenied
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render, reverse
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.decorators import permission_classes
from django_logger import logger
from members.models import APIKey
from transmission.forms.forms import SubmitJob
from transmission.scheduler import Scheduler, schedule_job
from .models import Uplink, Downlink, TLE
from .filters import TelemetryDownlinkFilter, TelemetryUplinkFilter, TLEFilter
#from .processing.save_raw_data import process_frames, store_frames
from .processing.save_raw_data import store_frames

QUERY_ROW_LIMIT = 100


@permission_classes([HasAPIKey, ])
def submit_frame(request):  # pylint:disable=R0911
    """Add frames to Uplink/Downlink table. The input is a list of json objects embedded in to the
    HTTP request."""

    #  TO DO: Add uplink/downlink identifier in the http request
    api_key_name = ""
    if request.method == 'POST':
        try:
            # retrieve the authorization header (if present, empty otherwise)
            key = request.META.get("HTTP_AUTHORIZATION", '')
            # retrieve the user agent (if present, empty otherwise)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # search for the username matching the API key
            api_key_name = APIKey.objects.get_from_key(key)
            # retrieve the JSON frame just submitted
            frame_to_add = json.loads(request.body)
            # add the frame to the database
            number_of_saved_frames = store_frames(frame_to_add, username=api_key_name, application=user_agent)

            logger.info("%s made a frame submission: %s frames saved.",
                        api_key_name, number_of_saved_frames)

            try:
                schedule_job("buffer_processing", date=datetime.now())
            except ValidationError as _:
                pass

            return JsonResponse({"result": "success",
                                 "message": f"Successful, {number_of_saved_frames} frames saved"},
                                status=HTTPStatus.CREATED)

        except APIKey.DoesNotExist as _:  # pylint:disable=C0103
            # catch a wrong API key
            logger.error("API key authentication error during frame submission")

            message_text = "Unauthorized request"
            return JsonResponse({"result": "failure", "message": message_text}, status=HTTPStatus.UNAUTHORIZED)

        except PermissionDenied as e:  # pylint:disable=C0103, W0612
            # catch submission without right permission
            logger.error("%s was denied permission to submit frame.", api_key_name)

            message_text = "Permission denied"
            return JsonResponse({"result": "failure", "message": message_text}, status=HTTPStatus.FORBIDDEN)

        except BadRequest as e:  # pylint:disable=C0103, W0612
            # catch submission without right permission
            logger.error("%s submitted a bad request.", api_key_name)

            return JsonResponse({"result": "failure", "message": str(e)}, status=HTTPStatus.BAD_REQUEST)

        except JSONDecodeError as e:  # pylint:disable=C0103, W0612
            # catch an error in the JSON request
            logger.error("%s submitted an invalid JSON structure.", api_key_name)

            message_text = "Invalid JSON structure"
            return JsonResponse({"result": "failure", "message": message_text}, status=HTTPStatus.BAD_REQUEST)

        except ValidationError as e:  # pylint:disable=C0103, W0612
            # catch an error in the frame formatting
            logger.error("%s submitted an invalid frame format.", api_key_name)
            return JsonResponse({"result": "failure", "message": str(e)}, status=HTTPStatus.BAD_REQUEST)

        except Exception as e:  # pylint:disable=C0103, W0703
            # catch other exceptions
            err_message = str(e)
            message_text = type(e).__qualname__ + ": " + err_message

            logger.error("%s submitted an invalid frame. Server error: %s", api_key_name, err_message)
            return JsonResponse({"result": "failure", "message": message_text}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # POST is the only supported method, return error
    return JsonResponse({"result": "failure", "message": "Method not allowed"}, status=HTTPStatus.METHOD_NOT_ALLOWED)


@login_required(login_url='/login')
def delete_processed_frames(request, link):
    """Remove the processed frames that are already stored in influxdb"""
    user = request.user

    if request.method != "POST":
        return HttpResponseBadRequest()

    if link not in ['uplink', 'downlink']:
        return HttpResponseBadRequest()

    if link == "uplink" and user.has_perm("transmission.delete_uplink"):
        buffered_frames = Uplink.objects.all().filter(processed=True)
    elif link == "downlink" and user.has_perm("transmission.delete_downlink"):
        buffered_frames = Downlink.objects.all().filter(processed=True)
    else:
        logger.warning("%s was denied permission to access uplink or downlink tables", request.user)
        return HttpResponseForbidden()

    removed_data_len = len(buffered_frames)
    buffered_frames.delete()

    messages.info(request, f"{removed_data_len} processed {link} frames were removed.")
    logger.info("%s frame buffer has been cleared.", link)
    return redirect('get_frames_table', link)


#@login_required(login_url='/login')
#def process(request, link):
#    """Process frames that are not already stored in influxdb"""
#
#    user = request.user
#
#    if link not in ['uplink', 'downlink']:
#        return HttpResponseBadRequest()
#
#    if link == "uplink" and user.has_perm("transmission.view_uplink"):
#        frames = Uplink.objects.all().filter(processed=False)
#        logger.info("%s frames processing triggered: %s frames to process", link, len(frames))
#
#        processed_frame_count = process_frames(frames, link)
#        logger.info("%s %s frames were successfully processed", processed_frame_count, link)
#
#        messages.info(request, f"{processed_frame_count} {link} frames were processed.")
#
#    elif link == "downlink" and user.has_perm("transmission.view_downlink"):
#        frames = Downlink.objects.all().filter(processed=False)
#        logger.info("%s frames processing triggered: %s frames to process", link, len(frames))
#
#        processed_frame_count = process_frames(frames, link)
#        logger.info("%s %s frames were successfully processed", processed_frame_count, link)
#
#        messages.info(request, f"{processed_frame_count} {link} frames were processed.")
#
#    else:
#        logger.warning("%s was denied permission to access uplink or downlink tables", request.user)
#        return HttpResponseForbidden()
#
#    return redirect('get_frames_table', link)


def paginate_telemetry_table(request, telemetry_filter, table_name):
    """Paginates a telemetry table and renders the filtering form"""

    data = telemetry_filter.qs
    paginator = Paginator(data, QUERY_ROW_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'telemetry_filter': telemetry_filter, 'page_obj': page_obj, 'table_name': table_name}
    return render(request, "transmission/table.html", context)

@login_required(login_url='/login')
def get_frames_table(request, link):
    """Queries and filters the uplink/downlink table"""

    if request.method != "GET" or link not in ['uplink', 'downlink']:
        return HttpResponseBadRequest()

    if link == "downlink" and request.user.has_perm('transmission.view_downlink'):
        frames = Downlink.objects.all().order_by('timestamp')
        telemetry_filter = TelemetryDownlinkFilter(request.GET, queryset=frames)
        return paginate_telemetry_table(request, telemetry_filter, "Downlink")

    if link == "uplink" and request.user.has_perm('transmission.view_uplink'):
        frames = Uplink.objects.all().order_by('timestamp')
        telemetry_filter = TelemetryUplinkFilter(request.GET, queryset=frames)
        return paginate_telemetry_table(request, telemetry_filter, "Uplink")

    logger.warning("%s was denied permission to access uplink or downlink tables.", request.user)
    return HttpResponseForbidden()


def get_tle_table(request):
    """Queries and filters the TLEs table"""
    if request.method != "GET":
        return HttpResponseBadRequest()

    frames = TLE.objects.all().order_by('valid_from')
    tle_filter = TLEFilter(request.GET, queryset=frames)

    data = tle_filter.qs
    paginator = Paginator(data, QUERY_ROW_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'telemetry_filter': tle_filter, 'page_obj': page_obj, 'table_name': 'TLE'}
    return render(request, "transmission/tle_table.html", context)


@login_required(login_url='/login')
def modify_scheduler(request, command):
    """Modify scheduler status: start, pause, resume, shutdown."""

    if request.method != 'POST':
        return HttpResponseBadRequest()

    if not request.user.is_superuser:
        return HttpResponseForbidden()

    scheduler = Scheduler()

    if command == "pause":
        scheduler.pause_scheduler()
    elif command == "shutdown":
        scheduler.stop_scheduler()
    elif command == "force_shutdown":
        scheduler.force_stop_scheduler()
    elif command == "start":
        scheduler.start_scheduler()
    elif command == "resume":
        scheduler.resume_scheduler()
    else:
        messages.error(request, "Invalid scheduler modification requested!")

    return HttpResponseRedirect(reverse("submit_job"))


@login_required(login_url='/login')
def submit_job(request):
    """Submit a task to be scheduled (scraping or bucket processing)"""

    if not request.user.is_superuser:
        return HttpResponseForbidden()

    form = SubmitJob(request.POST or None)
    submit_job_form = form

    scheduler = Scheduler()

    if request.method == 'POST':
        if form.is_valid():
            form_data = form.cleaned_data
            sat = form_data["sat"]
            job_type = form_data["job_type"]
            link = form_data["link"]
            date = form_data["datetime"]
            interval = form_data["interval"]

            try:
                schedule_job(job_type, sat, link, date, interval)
                messages.info(request, f"{sat} {job_type} {form_data['link']} submitted")

            except ValidationError as exception:
                messages.error(request, str(exception))

            return HttpResponseRedirect(reverse("submit_job"))

    running_jobs = scheduler.get_running_jobs()
    pending_jobs = scheduler.get_pending_jobs()

    return render(request,
                  'transmission/submit_job.html',
                  {'submit_job_form': submit_job_form,
                   'running_jobs': running_jobs,
                   'pending_jobs': pending_jobs,
                   'scheduler_status': scheduler.get_state()
                   }
                  )
