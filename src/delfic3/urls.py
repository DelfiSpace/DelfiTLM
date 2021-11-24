"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('delfic3/home/', views.home, name='delfic3_home'),
]
