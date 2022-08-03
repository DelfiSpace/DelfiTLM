"""API urls"""
import os
from django.urls import path
from . import views

urlpatterns = [
    path('delfipq/home/', views.home, name='delfipq_home'),
    # path('grafana/<path>/', views.GraphanaProxyView.as_view(),  name='graphana-delfi-pq'),
]

# add path only in debug mode
DEBUG = bool(int(os.environ.get('DEBUG', 1)))
dummy_tlm_path = path('delfipq/add-tlm/', views.add_dummy_tlm_data, name='delfi_pq_add_dummy_tlm')

if DEBUG:
    urlpatterns.append(dummy_tlm_path)
