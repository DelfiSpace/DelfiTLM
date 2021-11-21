"""Admin page for managing the database Delfipq models"""

from django.contrib import admin
from .models import Delfipq_L0_telemetry

admin.site.register(Delfipq_L0_telemetry)