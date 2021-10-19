"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('ewilgs/home/', views.home, name='ewilgs_home'),
]
