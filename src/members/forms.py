"""Customised forms for view/html files"""
from django import forms

class RegisterForm(forms.Form):
    """set password form"""
    username = forms.CharField(label="Username")
    email = forms.CharField(label="Email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())
    confirm_password = forms.CharField(label="Confirm password", widget=forms.PasswordInput())

class LoginForm(forms.Form):
    """login form"""
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

class ChangePasswordForm(forms.Form):
    """change password form"""
    current_password = forms.CharField(label="Current Password", widget=forms.PasswordInput())
    new_password = forms.CharField(label="New Password", widget=forms.PasswordInput())
    confirm_password = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput())
