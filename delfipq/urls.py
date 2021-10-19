"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('delfipq/home/', views.home, name='delfipq_home'),
]
