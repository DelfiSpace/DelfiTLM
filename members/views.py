"""API request handling. Map requests to the corresponding HTMLs."""
from django.shortcuts import render
from .forms import SetPasswordForm, LoginForm, ChangePasswordForm
from .models import Member
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from .backend.AuthenticationBackend import AuthenticationBackend

@login_required(login_url='/members/login')
def home(request):
    """render index.html page"""
    ren = render(request, "members/home/index.html")
    return ren

def setPassword(request):
    """render set.html page"""

    if request.method == 'POST':
        form = SetPasswordForm(request.POST)

        if form.is_valid():
            print("form valid")
            entered_username = form.cleaned_data['username']
            entered_password = form.cleaned_data['password']
            entered_confirmpassword = form.cleaned_data['confirm_password']

            if Member.objects.filter(username=entered_username).exists():

                member = Member.objects.get(username=entered_username)

                print(member.password)
                if member.password is None:
                    messages.info(request, "Password already exists")

                if entered_password == entered_confirmpassword:
                    Member.objects.filter(username=entered_username).update(
                        password=make_password(entered_password),
                        created_at=timezone.now(),
                        last_changed=timezone.now(),
                        active=True,
                    )
                    return render(request, "members/home/index.html")
                else:
                    messages.info(request, "Password and Confirm Password do not match")
                    return render(request, "members/set/set_password.html", {'form': form})

            else:
                messages.info(request, "User not found")
                return render(request, "members/set/set_password.html", {'form': form})
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
            print(entered_username)
            member = AuthenticationBackend.authenticate(request, username=entered_username, password=entered_password)
            print(member)

            if member is not None:
                login(request, member)
                return render(request, "members/home/index.html", {'form': form})
            else:
                messages.info(request, "User not found")
                return render(request, "members/home/login.html", {'form': form})

    return render(request, "members/home/login.html", { 'form': form })

def changePassword(request):

    form = ChangePasswordForm(request.POST)

    if request.method == "POST":
        if form.is_valid():
            entered_username = form.cleaned_data.get('username')
            entered_current_password = form.cleaned_data.get('current_password')
            entered_new_password = form.cleaned_data.get('new_password')
            entered_confirm_password = form.cleaned_data.get('confirm_password')

            member = authenticate(request, username=entered_username, password=entered_current_password)

            if member is not None:
                if entered_new_password == entered_confirm_password:
                    Member.objects.filter(username=entered_username).update(
                        password=make_password(entered_new_password),
                        created_at=timezone.now(),
                        last_changed=timezone.now(),
                        active=True,
                    )
                    member = authenticate(request, username=entered_username, password=entered_current_password)
                    login(request, member)
                    return render(request, "members/home/index.html", {'form': form })

    return render(request, "members/set/change_password.html", {'form': form })
