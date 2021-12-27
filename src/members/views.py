"""API request handling. Map requests to the corresponding HTMLs."""
import re
from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate, logout
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from .forms import RegisterForm, LoginForm, ChangePasswordForm
from .models import Member


def check_password(password):
    """Check the password for min 8 characters, min 1 upper and lower case letter,
    1 number and 1 special character"""

    regex_str = '^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$'
    regex = re.compile(regex_str)
    if regex.match(password):
        return True
    return False


@login_required(login_url='/members/login')
def profile(request):
    """Render profile page"""
    return render(request, "members/home/profile.html")


def register(request):
    """Render the register page and register a user"""

    form = RegisterForm(request.POST or None)

    if request.method == 'POST':

        if form.is_valid():
            entered_username = form.cleaned_data['username']
            entered_email = form.cleaned_data['email']
            entered_password = form.cleaned_data['password']
            entered_confirmpassword = form.cleaned_data['confirm_password']

            if Member.objects.filter(username=entered_username).exists():
                messages.info(request, "Username already exists")

            if entered_password == entered_confirmpassword:
                if check_password(entered_password):
                    member = Member.objects.create(
                        username=entered_username,
                        email=entered_email,
                        password=make_password(entered_password),
                        created_at=timezone.now(),
                        last_changed=timezone.now()
                    )
                    login(request, member)
                    return render(request, "members/home/profile.html")

                message="""Enter a password containing a minimum of 8 characters,
                    1 upper and lower case letter,
                    1 number and 1 special character."""
                messages.info(request, message)

            else:
                messages.info(request, "The password confirmation does not match")

    return render(request, "members/set/register.html", {'form': form })


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

            if member is not None and member.is_active is True:
                login(request, member)
                return render(request, "members/home/profile.html", {'form': form})

        messages.info(request, "Wrong username or password")

    return render(request, "members/home/login.html", { 'form': form })


@login_required(login_url='/members/login')
def logout_member(request):
    """Logout and reddirect to homepage"""
    logout(request)

    return redirect('homepage')


@login_required(login_url='/members/login')
def change_password(request):
    """Render change password page and reset password"""

    form = ChangePasswordForm(request.POST or None)
    username = request.user.username

    if request.method == "POST":
        if form.is_valid():
            entered_current_password = form.cleaned_data.get('current_password')
            entered_new_password = form.cleaned_data.get('new_password')
            entered_confirm_password = form.cleaned_data.get('confirm_password')

            member = authenticate(
                request,
                username=username,
                password=entered_current_password
            )

            if member is not None:
                if entered_new_password == entered_confirm_password:
                    if check_password(entered_new_password):
                        Member.objects.filter(username=username).update(
                            password=make_password(entered_new_password),
                            last_changed=timezone.now()
                        )
                        member = authenticate(
                            request,
                            username=username,
                            password=entered_current_password
                        )
                        login(request, member)
                        return render(request, "members/home/profile.html", {'form': form })

                    message="""Enter a password containing min 8 characters,
                    min 1 upper and lower case letter,
                    1 number and 1 special character"""
                    messages.info(request, message)
                else:
                    messages.info(request, "The password confirmation does not match")

            else:
                messages.info(request, "The current password does not match your password")

    return render(request, "members/set/change_password.html", {'form': form })


def reset_password(request):
    """Todo Render reset password page and reset password"""

    return redirect('homepage')
