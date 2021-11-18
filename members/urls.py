"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('members/home/', views.home, name='home'),
    path('members/set/', views.setPassword, name='set'),
    path('members/change/', views.changePassword, name='change'),
    path('members/login/', views.loginPage, name='login')
]
