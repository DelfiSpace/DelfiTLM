"""API urls"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('ewilgs/home/', views.home, name='home'),
    path('ewilgs/downlink/', views.get_downlink_table, name='ewilgs_downlink'),
    path('ewilgs/uplink/', views.get_uplink_table, name='ewilgs_uplink'),
    # add dummy data
    # path('add/', views.add_dummy_downlink_frames, name='add_dummy_downlink_frames'),
    path('submit_frame/', csrf_exempt(views.submit_frame), name='submit_frame'),
]
