"""API urls"""
from django.urls import path

from .views import home, getDownlinkFrames, addDownlinkFrames

urlpatterns = [
    path('ewilgs/home/', home, name='home'),
    path('ewilgs/downlink/', getDownlinkFrames, name='ewilgs_downlink'),
    path('ewilgs/downlink/addframe', addDownlinkFrames, name='addDownlinkFrames')
]
