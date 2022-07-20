"""API request handling. Map requests to the corresponding HTMLs."""
from django.shortcuts import render
from revproxy.views import ProxyView

class GraphanaProxyView(ProxyView):
    upstream = 'http://localhost:3000/grafana'

    def get_proxy_request_headers(self, request):
       headers = super(GraphanaProxyView, self).get_proxy_request_headers(request)
       headers['X-WEBAUTH-USER'] = "Bearer eyJrIjoiQlBXUzNEWkFKWnJZS2NZVWExM3pxSWllbTBPUmx3aGwiLCJuIjoiYWRtaW4iLCJpZCI6MX0="
       return headers

def home(request):
    """render index.html page"""
    ren = render(request, "delfipq/home/index.html")
    return ren
