"""API urls"""
from django.urls import path

from .views import home, get_downlink_frames, get_uplink_frames, add_downlink_frames

urlpatterns = [
    path('ewilgs/home/', home, name='home'),
    path('ewilgs/downlink/', get_downlink_frames, name='ewilgs_downlink'),
    path('ewilgs/uplink/', get_uplink_frames, name='ewilgs_uplink'),
    path('ewilgs/downlink/addframe', add_downlink_frames, name='add_downlink_frames')
]
