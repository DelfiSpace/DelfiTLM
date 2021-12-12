"""API urls"""
from django.urls import path

from .views import home, DownlinkView

urlpatterns = [
    path('ewilgs/home/', home, name='home'),
    path('ewilgs/Downlink/', DownlinkView, name='ewilgs_Downlink')
]
