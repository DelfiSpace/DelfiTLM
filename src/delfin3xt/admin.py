"""Admin page for managing the database models"""

from django.contrib import admin
from .models import Delfin3xt_L0_telemetry

@admin.register(Delfin3xt_L0_telemetry)
class Delfin3xt_L0_telemetry_Admin(admin.ModelAdmin): #pylint: disable=C0103
    """Registering to the delfin3xt telemetry to the admin interface"""
    pass #pylint: disable=W0107
