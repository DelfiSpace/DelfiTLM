"""API urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='homepage'),
    path("ban/", view=views.ban_view, name="ban_view"),
    path("test/", view=views.test_view, name="test_view"),

]
