"""API urls"""
from django.urls import path

from .views import home, getDownlinkFrames

urlpatterns = [
    path('ewilgs/home/', home, name='home'),
    path('ewilgs/Downlink/', getDownlinkFrames, name='ewilgs_Downlink')
]
