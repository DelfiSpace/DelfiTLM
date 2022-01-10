"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('ewilgs/home/', views.home, name='home'),
    path('ewilgs/downlink/', views.get_downlink_table, name='ewilgs_downlink'),
    path('ewilgs/uplink/', views.get_uplink_table, name='ewilgs_uplink'),
    # add dummy data COMMENT THIS IN PRODUCTION
    # path('add/downlink/', views.add_dummy_downlink_frames, name='add_dummy_downlink_frames'),
    path('submit/', views.submit, name='submit'),
]
