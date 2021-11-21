"""Admin page for managing the database Delfic3 models"""

from django.contrib import admin
from .models import Delfic3_L0_telemetry

admin.site.register(Delfic3_L0_telemetry)