"""Admin page for managing the database models"""

from django.contrib import admin
from .models import Downlink, Uplink

admin.site.register(Downlink)
admin.site.register(Uplink)
