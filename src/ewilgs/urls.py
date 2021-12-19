"""API urls"""
from django.urls import path

from .views import home, get_downlink_table, get_uplink_table, add_downlink_frames

urlpatterns = [
    path('ewilgs/home/', home, name='home'),
    path('ewilgs/downlink/', get_downlink_table, name='ewilgs_downlink'),
    path('ewilgs/uplink/', get_uplink_table, name='ewilgs_uplink'),
    path('ewilgs/downlink/addframe', add_downlink_frames, name='add_downlink_frames'),
]
