"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('members/profile/', views.profile, name='profile'),
    path('members/register/', views.register, name='register'),
    path('members/login/', views.login_member, name='login'),
    path('members/change/', views.change_password, name='change_password'),
    path('members/reset/', views.reset_password, name='reset_password'),
    path('members/logout/', views.logout_member, name='logout'),
    path('members/key/', views.generate_key, name='generate_key'),
    path('members/newkey/', views.get_new_key, name='get_new_key'),
]
