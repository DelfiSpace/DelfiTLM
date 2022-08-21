"""API request handling. Map requests to the corresponding HTMLs."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from delfipq.add_dummy_data import delfi_pq_add_dummy_tlm_data, delfi_pq_add_dummy_tlm_raw_data
from delfipq.process_raw_telemetry import process_frames_delfi_pq

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
    len_data = delfi_pq_add_dummy_tlm_data()

    return JsonResponse({"len": len_data})


def add_dummy_tlm_raw_data(request):
    """Add dummy raw telemetry"""
    len_data, stored_frames = delfi_pq_add_dummy_tlm_raw_data()
    return JsonResponse({"len": len_data, "len_stored": stored_frames})

def process_telemetry(request):
    """Trigger delfi_pq telemetry processing"""
    user = request.user

    if user.has_perm("transmission.view_downlink"):
        processed_frames_count, total_frames_count = process_frames_delfi_pq("downlink")
        message = f"{processed_frames_count}/{total_frames_count}"
        message += " delfi_pq telemetry frames processed"
        messages.info(request, message)
        return JsonResponse({"message": message})

    return PermissionDenied()


def home(request):
    """render index.html page"""
    ren = render(request, "delfipq/home/index.html")
    return ren
