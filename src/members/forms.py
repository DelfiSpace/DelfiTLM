"""Customized forms for view/html files"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, PasswordResetForm
from .models import Member

class RegisterForm(UserCreationForm):
    """Register user form"""
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)

    class Meta:
        """Meta class to specify db model"""
        model = Member
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']

        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    """login form"""
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())


class ChangePasswordForm(PasswordChangeForm):
    """Change password form"""
    class Meta:
        """Meta class to specify db model"""
        model = Member


class ForgotPasswordForm(PasswordResetForm):
    """reset password form"""
    class Meta:
        """Meta class to specify db model"""
        model = Member