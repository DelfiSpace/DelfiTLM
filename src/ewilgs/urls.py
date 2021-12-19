"""API urls"""
from django.urls import path

from .views import *

urlpatterns = [
    path('ewilgs/home/', home, name='home'),
    path('ewilgs/downlink/', get_downlink_frames, name='ewilgs_downlink'),
    path('ewilgs/uplink/', get_uplink_frames, name='ewilgs_uplink'),
    path('ewilgs/downlink/addframe/', add_downlink_frames, name='add_downlink_frames'),
    path('ewilgs/downlink/table/', get_downlink_table, name='get_downlink_table'),
    path('ewilgs/downlink/table/<int:pointer>/', get_next_frames, name='get_next_frames')
]
