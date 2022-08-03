"""API request handling. Map requests to the corresponding HTMLs."""
import json
from django.shortcuts import render
from delfipq import XTCEParser as xtce_parser
from delfipq.process_raw_telemetry import store_frame

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

        # process each frame
        for frame in data:
            try:
                store_frame(frame["timestamp"], frame["frame"], frame["observer"], "downlink")
            except xtce_parser.XTCEException as _:
                # ignore
                pass
    return {"len": len(data) }


def home(request):
    """render index.html page"""
    ren = render(request, "delfipq/home/index.html")
    return ren
