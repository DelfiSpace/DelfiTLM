"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('members/home/', views.home, name='home'),
]
