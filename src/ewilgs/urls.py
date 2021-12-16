"""API urls"""
from django.urls import path

from .views import home, get_downlink_frames, add_downlink_frames

urlpatterns = [
    path('ewilgs/home/', home, name='home'),
    path('ewilgs/downlink/', get_downlink_frames, name='ewilgs_downlink'),
    path('ewilgs/downlink/addframe', add_downlink_frames, name='add_downlink_frames')
]
