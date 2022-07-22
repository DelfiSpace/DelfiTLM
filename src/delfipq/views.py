"""API request handling. Map requests to the corresponding HTMLs."""
from django.shortcuts import render
from revproxy.views import ProxyView

class GraphanaProxyView(ProxyView):
    """Grafana proxy view for django"""
    upstream = 'http://localhost:3000/grafana'

    def get_proxy_request_headers(self, request):
        headers = super().get_proxy_request_headers(request)
        token = ""
        with open("src/tokens/grafana_token.txt", "r", encoding="utf-8") as file:
            token = file.read()
        headers['X-WEBAUTH-USER'] = token
        return headers

def home(request):
    """render index.html page"""
    ren = render(request, "delfipq/home/index.html")
    return ren
