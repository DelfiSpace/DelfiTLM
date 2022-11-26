"""API urls"""
from django.urls import path

from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('account/', views.account, name='account'),

    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.verify, name='activate'),
    path('resend-verification-email/', views.resend_verification_email, name='resend_verify'),
    path('update-email/', views.change_email_request, name="change_email"),

    path('login/', views.login_member, name='login'),
    path('logout/', views.logout_member, name='logout'),

    path('change-password/', views.change_password, name='change_password'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
        ),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'
         ),

    path('key/', views.generate_key, name='generate_key'),
    path('new-key/', views.get_new_key, name='get_new_key'),

    path('delete-account', views.delete_account_request, name='delete_account'),
]
