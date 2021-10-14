"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('delfin3xt/home/', views.home, name='delfin3xt_home'),
]
