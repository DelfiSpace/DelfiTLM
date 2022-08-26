"""API urls"""
import os
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path('transmission/<link>/', views.get_frames_table, name='get_frames_table'),
    path('transmission/process-frames/<link>/', views.process, name='process'),
    path('transmission/process-bucket/<satellite>/<link>/',
         views.process_raw_telemetry_bucket,
         name='process_raw_telemetry_bucket'
         ),
    path('transmission/delete-processed-frames/<link>/',
         views.delete_processed_frames,
         name='delete_processed_frames'
         ),
    path('TLEs/', views.get_tle_table, name='get_tle_table'),
    path('submit/', csrf_exempt(views.submit_frame), name='submit_frame'),
    path('schedule-job/', csrf_exempt(views.submit_job), name='submit_job'),
]

# add path only in debug mode
dummy_data_path = path('add/', views.add_dummy_downlink_frames, name='add_dummy_downlink_frames')
DEBUG = bool(int(os.environ.get('DEBUG', 1)))

if DEBUG:
    urlpatterns.append(dummy_data_path)
