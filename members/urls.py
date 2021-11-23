"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('members/home/', views.home, name='home'),
    path('members/register/', views.register, name='register'),
    path('members/login/', views.login_member, name='login'),
    path('members/change/', views.change_password, name='change'),
]
