"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('members/home/', views.home, name='home'),
    path('members/set/', views.set_password, name='set'),
    path('members/login/', views.login_member, name='login'),
    path('members/change/', views.change_password, name='change'),
]
