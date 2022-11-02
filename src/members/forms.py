"""Customized forms for view/html files"""
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, PasswordChangeForm
from .models import Member


class RegisterForm(UserCreationForm):
    """Register user form"""
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    latitude = forms.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    longitude = forms.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)]
    )

    class Meta:
        """Meta class to specify db model"""
        model = Member
        fields = ("username", "email", "password1", "password2", "latitude", "longitude")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["username"]
        user.latitude = self.cleaned_data["latitude"]
        user.longitude = self.cleaned_data["longitude"]

        if commit:
            user.save()
        return user


class ResendVerificationForm(forms.Form):
    """Resend verification email form"""
    email = forms.EmailField(required=True)


class LoginForm(forms.Form):
    """Login form"""
    username = forms.CharField(label="Username or email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())


class ChangeEmailForm(forms.Form):
    """Change email form"""
    email = forms.EmailField(label="New email address", required=True)
    email_confirm = forms.EmailField(label="Confirm the ew email address", required=True)


class ChangePasswordForm(PasswordChangeForm):
    """Change password form"""
    class Meta:
        """Meta class to specify db model"""
        model = Member


class ForgotPasswordForm(PasswordResetForm):
    """Reset password form"""
    class Meta:
        """Meta class to specify db model"""
        model = Member


class DeleteAccountForm(forms.Form):
    """Delete account form"""
    username = forms.CharField(label="Username")
    challenge = forms.CharField(label='Type "delete my account" to confirm')
    password = forms.CharField(label="Password", widget=forms.PasswordInput())
