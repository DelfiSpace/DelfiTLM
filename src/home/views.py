"""API request handling. Map requests to the corresponding HTMLs."""
import os
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from pycrowdsec.client import StreamClient

def home(request):
    """Render index.html page"""
    ren = render(request, "home/index.html")
    return ren

def ban_view(request):
    """Ban request"""
    raise PermissionDenied

def test_view(request):
    """Test connection to crowdsec"""
    client = StreamClient(
        api_key=os.environ.get('CROWDSEC_LAPI'),
        lapi_url=os.environ.get('CROWDSEC_URL')
    )

    client.run()
    assert client.get_action_for("127.0.0.1") != "ban"

    return render(request, "home/index.html")
