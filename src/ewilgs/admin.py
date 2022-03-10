"""Admin page for managing the database models"""

from django.contrib import admin
from .models import Downlink, Uplink, TLE, Satellite

admin.site.register(Downlink)
admin.site.register(Uplink)
admin.site.register(TLE)
admin.site.register(Satellite)
