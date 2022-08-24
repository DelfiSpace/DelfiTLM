"""API urls"""
import os
from django.urls import path
from . import views

urlpatterns = [
    path('delfipq/home/', views.home, name='delfipq_home'),
    path('delfipq/process-tlm/', views.process_telemetry, name="delfi_pq_process_tlm")
    # path('grafana/<path>/', views.GraphanaProxyView.as_view(),  name='graphana-delfi-pq'),
]

# add path only in debug mode
DEBUG = bool(int(os.environ.get('DEBUG', 1)))
