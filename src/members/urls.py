"""API urls"""
from django.urls import path

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('members/profile/', views.profile, name='profile'),
    path('members/register/', views.register, name='register'),
    path('members/login/', views.login_member, name='login'),
    path('members/change/', views.change_password, name='change_password'),
    path('members/logout/', views.logout_member, name='logout'),
    path('members/key/', views.generate_key, name='generate_key'),
    path('members/newkey/', views.get_new_key, name='get_new_key'),
    path('members/activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('members/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('members/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('members/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('members/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
