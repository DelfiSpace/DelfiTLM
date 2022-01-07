"""API request handling. Map requests to the corresponding HTMLs."""
from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import RegisterForm, LoginForm, ChangePasswordForm
from .models import Member

@login_required(login_url='/members/login')
def profile(request):
    """Render profile page"""
    return render(request, "members/home/profile.html")


def register(request):
    """Render the register page and register a user"""

    form = RegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)
            Member.objects.filter(username=user.username).update(
                        date_joined=timezone.now(),
                        last_login=timezone.now()
                    )
            return render(request, "members/home/profile.html")
        messages.error(request, "Unsuccessful registration. Invalid information.")

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
                Member.objects.filter(username=member.username).update(
                        last_login=timezone.now()
                    )
                return render(request, "members/home/profile.html")

        messages.info(request, "Invalid username or password")

    return render(request, "members/home/login.html", { 'form': form })


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
        else:
            messages.info(request, "Invalid password")

    return render(request, "members/set/change_password.html", {'form': form })


def reset_password(request):
    """Todo Render reset password page and reset password"""

    return redirect('homepage')
