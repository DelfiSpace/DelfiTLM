"""API request handling. Map requests to the corresponding HTMLs."""
import json
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
from delfipq import XTCEParser as xtce_parser
from delfipq.process_raw_telemetry import process_frames_delfi_pq, store_frame, store_raw_frame

# from revproxy.views import ProxyView

# class GraphanaProxyView(ProxyView):
#     """Grafana proxy view for django"""
#     upstream = 'http://localhost:3000/grafana'

#     def get_proxy_request_headers(self, request):
#         headers = super().get_proxy_request_headers(request)
#         token = ""
#         with open("tokens/grafana_token.txt", "r", encoding="utf-8") as file:
#             token = file.read()
#         headers['X-WEBAUTH-USER'] = token
#         return headers


def add_dummy_tlm_data(request):
    """Add dummy processed telemetry intended to test and experiment with dashboards."""
    inputfile = "delfipq/delfi-pq.txt"
    with open(inputfile, encoding="utf-8") as file:
        data = json.load(file)
        # sort messages in chronological order
        data.sort(key=lambda x: x["timestamp"])
        # data = data[:100]
        # process each frame
        for frame in data:
            try:
                store_frame(frame["timestamp"], frame["frame"], frame["observer"], "downlink")
            except xtce_parser.XTCEException as _:
                # ignore
                pass
    return JsonResponse({"len": len(data)})


def add_dummy_tlm_raw_data(request):
    """Add dummy raw telemetry"""
    inputfile = "delfipq/delfi-pq.txt"
    stored_frames = 0
    with open(inputfile, encoding="utf-8") as file:
        data = json.load(file)
        # sort messages in chronological order
        data.sort(key=lambda x: x["timestamp"])
        data = data[:100]
        # process each frame
        for frame in data:
            stored = store_raw_frame(frame["timestamp"],
                                     frame["frame"],
                                     frame["observer"],
                                     "downlink")
            if stored:
                stored_frames += 1

    return JsonResponse({"len": len(data), "len_stored": stored_frames})


def process_telemetry(request):
    """Trigger delfi_pq telemetry processing"""
    user = request.user

    if user.has_perm("transmission.view_downlink"):
        processed_frames_count, total_frames_count = process_frames_delfi_pq("downlink")
        message = f"{processed_frames_count}/{total_frames_count}"
        message += " Delfi-PQ telemetry frames processed"
        messages.info(request, message)

    else:
        message =  "Operation not allowed"
        messages.error(request, message)

    return JsonResponse({"message": message})




def home(request):
    """render index.html page"""
    ren = render(request, "delfipq/home/index.html")
    return ren
