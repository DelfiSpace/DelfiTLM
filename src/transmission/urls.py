"""API urls"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path('transmission/<link>/', views.get_frames_table, name='get_frames_table'),
    path('transmission/delete-processed-frames/<link>/', views.delete_processed_frames, name='delete_processed_frames'),
    # path('TLEs/', views.get_tle_table, name='get_tle_table'),
    path('submit/', csrf_exempt(views.submit_frame), name='submit_frame'),
    path('schedule-job/', views.submit_job, name='submit_job'),
    path('modify-scheduler/<command>/', views.modify_scheduler, name='modify_scheduler'),
]
