"""API request handling. Map requests to the corresponding HTMLs."""
import json
import os
from django.http.response import JsonResponse
from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from .forms import RegisterForm, LoginForm, ChangePasswordForm
from .models import APIKey, Member
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage


@login_required(login_url='/members/login')
def profile(request):
    """Render profile page"""
    return render(request, "members/home/profile.html")


def register(request):
    """Render the register page and register a user"""

    form = RegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            # login(request, user)
            # Member.objects.filter(username=user.username).update(
            #             date_joined=timezone.now(),
            #             last_login=timezone.now()
            #         )

            # send_mail(
            #     'Welcome to the DelfiTLM portal!',
            #     'Dear ' + user.username +
            #     ',\n thank you for joining the DelfiTLM portal: with this portal,'
            #     ' you can submit telemetry for all the DelfiSpace satellites. ',
            #     os.environ.get('EMAIL_FROM',''),
            #     [user.email],
            #     fail_silently=True,
            #     )
            current_site = get_current_site(request)

            message = render_to_string('members/set/Register_email_verification.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = user.email
            send_mail( subject="Welcome to DelfiTLM",
                message=message,
                from_email = None,
                recipient_list = [to_email],
                fail_silently=True,
                )
            return HttpResponse('Please confirm your email address to complete the registration')

        messages.error(request, "Unsuccessful registration. Invalid information.")

    return render(request, "members/set/register.html", {'form': form })

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = Member.objects.get(pk=uid)

    except(TypeError, ValueError, OverflowError):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.verified = True
        user.save()
        login(request, user)
        Member.objects.filter(username=user.username).update(
                    date_joined=timezone.now(),
                    last_login=timezone.now()
                )
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')

def login_member(request):
    """Render login page"""

    form = LoginForm(request.POST or None)

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
                messages.info(request, "User not verified")
                return render(request, "members/home/login.html", {'form': form})

            if member is not None and member.is_active is True:
                login(request, member)
                Member.objects.filter(username=member.username).update(
                        last_login=timezone.now()
                    )
                return render(request, "members/home/profile.html")

        messages.info(request, "Invalid username or password")

    return render(request, "members/home/login.html", { 'form': form })


@login_required(login_url='/members/login')
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


@login_required(login_url='/members/login')
def get_new_key(request):
    """Render profile page with API key"""

    key = json.loads(generate_key(request).content)['generated_key']
    context = {'key': key}
    return render(request, "members/home/profile.html", context)


@login_required(login_url='/members/login')
def logout_member(request):
    """Logout and reddirect to homepage"""
    logout(request)

    return redirect('homepage')


@login_required(login_url='/members/login')
def change_password(request):
    """Render change password page and reset password"""

    form = ChangePasswordForm(request.user)

    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            Member.objects.filter(username=user.username).update(
                        last_changed=timezone.now()
                    )
            return redirect('profile')

        messages.info(request, "Invalid password")

    return render(request, "members/set/change_password.html", {'form': form })


def reset_password(request):
    """Todo Render reset password page and reset password"""

    return redirect('homepage')
