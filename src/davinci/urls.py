"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('davinci/home/', views.home, name='davinci_home'),
]
