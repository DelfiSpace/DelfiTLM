"""API request handling. Map requests to the corresponding HTMLs."""
from django.shortcuts import render
from .forms import SetPasswordForm, LoginForm, ChangePasswordForm
from .models import Members, Passwords
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from .backend.AuthenticationBackend import AuthenticationBackend
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.decorators import login_required

@login_required(login_url="members/login/login.html")
def home(request):
    """render index.html page"""
    ren = render(request, "members/home/index.html")
    return ren

def setPassword(request):
    """render set.html page"""

    if request.method == 'POST':
        form = SetPasswordForm(request.POST)

        if form.is_valid():
            entered_username = form.cleaned_data['username']
            entered_password = form.cleaned_data['password']
            entered_confirmpassword = form.cleaned_data['confirm_password']

            if Members.objects.filter(username=entered_username).exists():

                if Passwords.objects.filter(username=entered_username).exists():
                    messages.info(request, "Password already exists")
                    return render(request, "members/home/index.html")

                if entered_password == entered_confirmpassword:
                    password = form.save(commit=False)
                    member = Members.objects.get(username=entered_username)
                    password.member_id_id = member.UUID
                    password.UUID = member.UUID
                    password.username = entered_username
                    password.password = make_password(entered_password)
                    password.last_chaged = timezone.now()
                    password.save()
                    return render(request, "members/home/index.html")
                else:
                    messages.info(request, "Password and Confirm Password do not match")
                    return render(request, "members/set/set_password.html", {'form': form})

            else:
                print("user not found")
        else:
            form.errors
            return render(request, "members/set/set_password.html", {'form': form })
    else:
        form = SetPasswordForm()
        print("request method != POST")

    return render(request, "members/set/set_password.html", {'form': form })

def loginPage(request):

    form = LoginForm(request.POST)

    if request.method == "POST":
        if form.is_valid():
            entered_username = form.cleaned_data.get('username')
            entered_password = form.cleaned_data.get('password')
            member = AuthenticationBackend.authenticate(request, username=entered_username, password=entered_password)

            if member is not None:
                try:
                    authenticate.login(request, member)
                except AttributeError:
                    print("")
                return render(request, "members/home/index.html", {'form': form})
            else:
                return render(request, "members/login/login.html", {'form': form})

    return render(request, "members/home/login.html", { 'form': form })

# WIP
def changePassword(request):

    form = ChangePasswordForm(request.POST)

    if request.method == "POST":
        if form.is_valid():
            entered_username = form.cleaned_data.get('username')
            entered_current_password = form.cleaned_data.get('current_password')
            entered_new_password = form.cleaned_data.get('new_password')
            entered_confirm_password = form.cleaned_data.get('confirm_password')

            member = AuthenticationBackend.authenticate(request, username=entered_username, password=entered_current_password)
            print(member)
            if member is not None:
                if entered_new_password == entered_confirm_password:
                    print("password matches")
                    newPassword = Passwords.objects.get(username=entered_username)
                    newPassword.password = make_password(entered_new_password)
                    newPassword.last_changed = timezone.now()
                    newPassword.save()
                    return home

    return render(request, "members/set/change_password.html", {'form': form })







