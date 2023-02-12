"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='homepage'),
    path('location/<norad_id>/', views.get_satellite_location_now_api, name='sat_location'),
    path("ban/", view=views.ban_view, name="ban_view"),
    path("test/", view=views.test_view, name="test_view"),

]
