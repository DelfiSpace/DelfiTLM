"""API request handling. Map requests to the corresponding HTMLs."""
from django.shortcuts import render
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from .forms import RegisterForm, LoginForm, ChangePasswordForm
from .models import Member
from .backend.authentication_backend import AuthenticationBackend

@login_required(login_url='/members/login')
def home(request):
    """render index.html page"""
    ren = render(request, "members/home/index.html")
    return ren

def register(request):
    """render set.html page"""

    form = RegisterForm(request.POST or None)

    if request.method == 'POST':

        if form.is_valid():
            entered_username = form.cleaned_data['username']
            entered_email = form.cleaned_data['email']
            entered_password = form.cleaned_data['password']
            entered_confirmpassword = form.cleaned_data['confirm_password']

            if Member.objects.filter(username=entered_username).exists():
                messages.info(request, "Member already exists")

            if entered_password == entered_confirmpassword:
                Member.objects.create(
                    username=entered_username,
                    email=entered_email,
                    password=make_password(entered_password),
                    created_at=timezone.now(),
                    last_changed=timezone.now(),
                    active=True,
                )

                return render(request, "members/home/index.html")
    # messages.info("Wrong password or no user found")
    return render(request, "members/set/set_password.html", {'form': form })

def login_member(request):
    """Render login page"""

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            entered_username = form.cleaned_data.get('username')
            entered_password = form.cleaned_data.get('password')

            member = AuthenticationBackend().authenticate(
                request,
                username=entered_username,
                password=entered_password
            )

            if member is not None:
                login(request, member)
                print("logged in")
                return render(request, "members/home/index.html", {'form': form})

        messages.info(request, "Wrong password or user does not exist")

    return render(request, "members/home/login.html", { 'form': form })

def change_password(request):
    """Render change password page"""

    form = ChangePasswordForm(request.POST)

    if request.method == "POST":
        if form.is_valid():
            entered_username = form.cleaned_data.get('username')
            entered_current_password = form.cleaned_data.get('current_password')
            entered_new_password = form.cleaned_data.get('new_password')
            entered_confirm_password = form.cleaned_data.get('confirm_password')

            member = authenticate(
                request,
                username=entered_username,
                password=entered_current_password
            )

            if member is not None:
                if entered_new_password == entered_confirm_password:
                    Member.objects.filter(username=entered_username).update(
                        password=make_password(entered_new_password),
                        last_changed=timezone.now(),
                        active=True,
                    )
                    member = authenticate(
                        request,
                        username=entered_username,
                        password=entered_current_password
                    )
                    login(request, member)
                    return render(request, "members/home/index.html", {'form': form })

    return render(request, "members/set/change_password.html", {'form': form })
