"""API urls"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('transmission/<link>/', views.get_frames_table, name='get_frames_table'),
    path('transmission/tle/', views.get_tle_table, name='get_tle_table'),
    path('transmission/delete-processed-frames/<link>/',
         views.delete_processed_frames, name='delete_processed_frames'),
    path('transmission/process-frames/<link>/', views.process, name='process'),
    # add dummy data
    path('add/', views.add_dummy_downlink_frames, name='add_dummy_downlink_frames'),
    path('submit/', csrf_exempt(views.submit_frame), name='submit_frame'),
]
