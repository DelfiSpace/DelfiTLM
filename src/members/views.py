"""API request handling. Map requests to the corresponding HTMLs."""
from http import HTTPStatus
import json
from django.http.response import JsonResponse
from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_text
from django.utils.http import  urlsafe_base64_decode
from .send_emails import send_welcome_email, send_email_verification_registration, \
    send_password_reset_email, send_confirm_account_deleted_email
from .forms import DeleteAccountForm, RegisterForm, LoginForm, ChangePasswordForm, \
    PasswordResetForm, ResendVerificationForm
from .models import APIKey, Member


@login_required(login_url='/login')
def account(request):
    """Render account page"""
    return render(request, "account.html")


def register(request):
    """Render the register page and register a user"""

    status = HTTPStatus.OK
    form = RegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save(commit=False)
            user.date_joined=timezone.now()
            user.save()
            send_welcome_email(user)
            send_email_verification_registration(request, user)
            message = "Please confirm your email address to complete the registration."
            messages.info(request, message)
            return redirect("homepage")

        messages.error(request, "Unsuccessful registration")
        status = HTTPStatus.BAD_REQUEST

    return render(request, "registration/register.html", {'form': form}, status=status)


def verify(request, uidb64, token):
    """Verify user email"""
    status = HTTPStatus.OK
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = Member.objects.get(pk=uid)

    except(TypeError, ValueError, OverflowError):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.verified = True
        user.save()

        login(request, user)
        Member.objects.filter(username=user.username).update(last_login=timezone.now())

        messages.info(request, "Your email has been successfully verified.")
    else:
        messages.error(request, 'Verification link is invalid or expired!')
        status = HTTPStatus.BAD_REQUEST
    return render(request, "home/index.html", status=status)


def resend_verification_email(request):
    """Resent verification emails, in case it's not received."""
    form = ResendVerificationForm(request.POST or None)
    status = HTTPStatus.OK

    if request.method == "POST":
        if form.is_valid():
            entered_email = form.cleaned_data.get('email')
            if Member.objects.filter(email=entered_email).exists():
                user = Member.objects.get(email=entered_email)
                if not user.verified:
                    send_email_verification_registration(request, user)
                    messages.info(request, "The verification email has been resent.")
                    return redirect('login')

        status = HTTPStatus.BAD_REQUEST
        messages.error(request, "Email is unknown or is already verified!")

    return render(request, "registration/resend_verification_email.html",
                  context={ 'form': form }, status=status)


def login_member(request):
    """Render login page"""

    form = LoginForm(request.POST or None)
    status = HTTPStatus.OK

    if request.method == "POST":
        if form.is_valid():
            entered_username = form.cleaned_data.get('username')
            entered_password = form.cleaned_data.get('password')

            member = authenticate(
                request,
                username=entered_username,
                password=entered_password
            )

            if member is not None and member.verified is False:
                messages.error(request, "Email not verified!")
                return redirect("resend_verify")

            if member is not None and member.is_active is True:
                login(request, member)
                Member.objects.filter(username=member.username).update(
                        last_login=timezone.now()
                    )
                return redirect("account")

        messages.error(request, "Invalid username or password!")
        status = HTTPStatus.UNAUTHORIZED

    return render(request, "registration/login.html", context={ 'form': form }, status=status)


@login_required(login_url='/login')
def generate_key(request):
    """Generates an API key"""

    if len(APIKey.objects.filter(name=request.user.username))!=0:
        key = APIKey.objects.filter(name=request.user.username)
        key.delete()


    api_key_name, generated_key = APIKey.objects.create_key(
                            name=request.user.username,
                            username=Member.objects.get(username=request.user.username),
    )

    return JsonResponse({"api_key": str(api_key_name), "generated_key": str(generated_key)})


@login_required(login_url='/login')
def get_new_key(request):
    """Render account page with API key"""

    key = json.loads(generate_key(request).content)['generated_key']
    context = {'key': key}
    return render(request, "account.html", context)


@login_required(login_url='/login')
def logout_member(request):
    """Logout and redirect to homepage"""
    logout(request)

    return redirect('homepage')


@login_required(login_url='/login')
def change_password(request):
    """Render change password page and reset password"""

    form = ChangePasswordForm(request.user)
    status = HTTPStatus.OK

    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            Member.objects.filter(username=user.username).update(
                        last_changed=timezone.now()
                    )
            messages.info(request, "Password has been changed successfully.")
            return redirect('account')

        messages.error(request, "Invalid password!")
        status = HTTPStatus.BAD_REQUEST

    return render(request, "registration/change_password.html", {'form': form }, status=status)


def password_reset_request(request):
    """Send password recovery email"""

    form = PasswordResetForm(request.POST or None)
    status = HTTPStatus.OK

    if request.method == "POST":
        if form.is_valid():
            entered_email = form.cleaned_data['email']
            if Member.objects.filter(email=entered_email).exists():
                user = Member.objects.get(email=entered_email)
                send_password_reset_email(request, user)
                message = "A message with reset password instructions has been sent to your inbox."
                messages.info(request, message)
                return redirect("homepage")

        messages.error(request, "Invalid email address")
        status = HTTPStatus.BAD_REQUEST

    return render(request, "registration/password_reset_form.html", {'form': form}, status=status)


@login_required(login_url='/login')
def delete_account_request(request):
    """Delete user account upon request."""

    form = DeleteAccountForm(request.POST or None)
    status = HTTPStatus.OK

    if request.method == "POST":
        if form.is_valid():

            entered_username = form.cleaned_data.get('username')
            entered_password = form.cleaned_data.get('password')
            entered_challenge = form.cleaned_data.get('challenge')

            user = authenticate(
                request,
                username=entered_username,
                password=entered_password
            )

            if user is not None and entered_challenge == "delete my account":
                user = Member.objects.get(username=entered_username)
                send_confirm_account_deleted_email(user)
                user.delete()
                messages.info(request, "Your account has been deleted.")
                logout(request)
                return redirect("homepage")

            if user is None:
                messages.error(request, "Invalid username or password!")
                status = HTTPStatus.BAD_REQUEST

            elif user is not None and entered_challenge != "delete my account":
                messages.error(request, "Confirmation failed! Account was not deleted.")
                status = HTTPStatus.BAD_REQUEST
        else:
            status = HTTPStatus.BAD_REQUEST

    return render(request, "registration/delete_account_form.html", {'form': form}, status=status)
