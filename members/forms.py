from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Passwords

class SetPasswordForm(forms.ModelForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="password")
    confirm_password = forms.CharField(label="confirm password")

    class Meta:
        model = Passwords
        fields = ["username", "password"]

class LoginForm(forms.ModelForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="password")

    class Meta:
        model = Passwords
        fields = ["username", "password"]
