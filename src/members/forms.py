"""Customised forms for view/html files"""
from django import forms

class RegisterForm(forms.Form):
    """set password form"""
    username = forms.CharField(label="Username")
    email = forms.CharField(label="email")
    password = forms.CharField(label="password")
    confirm_password = forms.CharField(label="confirm password")

class LoginForm(forms.Form):
    """login form"""
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password")

class ChangePasswordForm(forms.Form):
    """change password form"""
    username = forms.CharField(label="Username")
    current_password = forms.CharField(label="Current Password")
    new_password = forms.CharField(label="New Password")
    confirm_password = forms.CharField(label="Confirm New Password")
