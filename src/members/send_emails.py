"""Functions sending emails to users."""
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django_logger import logger
import traceback

def get_protocol(request):
    """Return the HTTP or HTTPS based on
    the protocol chosen in the request."""

    if request.is_secure():
        return 'https'
    return 'http'

def send_welcome_email(user):
    """Send welcome email to new users."""
    email_template = "emails/welcome_email.html"
    subject = "Welcome to DelfiTLM!"

    message = render_to_string(email_template, {
        'username': user.username,
    })

    try:    
        send_mail(
            subject=subject,
            message=message,
            from_email = None,
            recipient_list = [user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error("Email backend: %s", str(settings.EMAIL_BACKEND))
        logger.error("Email host: %s", str(settings.EMAIL_HOST))
        logger.error("Email port: %s", str(settings.EMAIL_PORT))
        logger.error("Send_email failure:\n%s", traceback.format_exc())

def send_confirm_account_deleted_email(user):
    """Send a confirmation that the user account has been deleted."""

    email_template = "emails/deleted_account_confirmation_email.html"
    subject = "Account deletion"

    message = render_to_string(email_template, {
        'username': user.username,
    })

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email = None,
            recipient_list = [user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error("Email backend: %s", str(settings.EMAIL_BACKEND))
        logger.error("Email host: %s", str(settings.EMAIL_HOST))
        logger.error("Email port: %s", str(settings.EMAIL_PORT))
        logger.error("Send_email failure:\n%s", traceback.format_exc())

def _send_email_with_token(request, user, email_template, subject, email=None):
    """Helper method sending an email containing a verification token.
    User for email verification and password reset."""
    protocol = get_protocol(request)
    current_site = get_current_site(request)

    if email is None:
        email = user.email

    message = render_to_string(email_template, {
        'user': user,
        'email': email,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
        'protocol': protocol
    })

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email = None,
            recipient_list = [email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error("Email backend: %s", str(settings.EMAIL_BACKEND))
        logger.error("Email host: %s", str(settings.EMAIL_HOST))
        logger.error("Email port: %s", str(settings.EMAIL_PORT))
        logger.error("Send_email failure:\n%s", traceback.format_exc())

def send_email_verification_registration(request, user):
    """Sends an email to verify the email address of a newly registered user."""
    email_template = "emails/register_email_verification.html"
    subject = "Verify your email"

    _send_email_with_token(request, user, email_template, subject)

def send_email_change_request_confirmation(user):
    """Sends an email the current email address to confirm it should be changed."""

    email_template = "emails/confirm_email_address_change.html"
    subject = "Email address change requested"

    try:
        send_mail(
             subject=subject,
             message=render_to_string(email_template, {
                 'email': user.email
             }),
             from_email = None,
             recipient_list = [user.email],
             fail_silently=False,
        )
    except Exception as e:
        logger.error("Email backend: %s", str(settings.EMAIL_BACKEND))
        logger.error("Email host: %s", str(settings.EMAIL_HOST))
        logger.error("Email port: %s", str(settings.EMAIL_PORT))
        logger.error("Send_email failure:\n%s", traceback.format_exc())

def send_new_email_verification(request, user):
    """Upon email update request, sends an email the new email address to verify it."""
    email_template = "emails/verify_new_email.html"
    subject = "Verify your new email"
    _send_email_with_token(request, user, email_template, subject, email=user.new_email)

def send_password_reset_email(request, user):
    """Sends a password reset email with a link to the reset form."""
    email_template = "emails/password_reset_email.html"
    subject = "Password Reset Requested"
    _send_email_with_token(request, user, email_template, subject)
