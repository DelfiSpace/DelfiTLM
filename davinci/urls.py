"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('davinci_home/', views.home),
]
