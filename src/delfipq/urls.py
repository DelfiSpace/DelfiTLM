"""API urls"""
import os
from django.urls import path
from . import views

urlpatterns = [
    path('delfipq/process-tlm/', views.process_telemetry, name="delfi_pq_process_tlm")
]

# add path only in debug mode
DEBUG = bool(int(os.environ.get('DEBUG', 1)))
