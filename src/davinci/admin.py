"""Admin page for managing the database Da Vinci models"""

from django.contrib import admin
from .models import DaVinci_L0_telemetry

admin.site.register(DaVinci_L0_telemetry)
