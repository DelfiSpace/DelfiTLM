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
dummy_tlm_path = path('delfipq/add-tlm/',
                      views.add_dummy_tlm_data,
                      name='delfi_pq_add_dummy_tlm'
                      )
dummy_raw_tlm_path =  path('delfipq/add-raw-tlm/',
                           views.add_dummy_tlm_raw_data,
                           name='delfi_pq_add_dummy_raw_tlm'
                           )

if DEBUG:
    urlpatterns.append(dummy_tlm_path)
    urlpatterns.append(dummy_raw_tlm_path)
