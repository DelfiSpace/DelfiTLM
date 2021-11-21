from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Member

class SetPasswordForm(forms.Form):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="password")
    confirm_password = forms.CharField(label="confirm password")

    # class Meta:
    #     model = Member
    #     fields = ["username", "password"]

class LoginForm(forms.Form):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password")

    # class Meta:
    #     model = Passwords
    #     fields = ["username", "password"]

class ChangePasswordForm(forms.Form):
    username = forms.CharField(label="Username")
    current_password = forms.CharField(label="Current Password")
    new_password = forms.CharField(label="New Password")
    confirm_password = forms.CharField(label="Confirm New Password")

    # class Meta:
    #     model = Passwords
    #     fields = ["username", "current_password", "new_password", "confirm_password"]
