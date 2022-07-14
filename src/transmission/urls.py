"""API urls"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('transmission/downlink/', views.get_downlink_table, name='transmission_downlink'),
    path('transmission/uplink/', views.get_uplink_table, name='transmission_uplink'),
    path('transmission/tle/', views.get_tle_table, name='get_tle_table'),
    # add dummy data
    # path('add/', views.add_dummy_downlink_frames, name='add_dummy_downlink_frames'),
    path('submit/', csrf_exempt(views.submit_frame), name='submit_frame'),
]
