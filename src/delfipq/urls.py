"""API urls"""
from django.urls import path, URLPattern

from . import views

urlpatterns = [
    path('delfipq/home/', views.home, name='delfipq_home'),
    path('grafana/<path>/', views.GraphanaProxyView.as_view(),  name='graphana-delfi-pq'),
]
