"""API request handling. Map requests to the corresponding HTMLs."""
from django.shortcuts import render
from .forms import SetPasswordForm, LoginForm
from .models import Members, Passwords
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password

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
                    print("password exists, need to make change password page")
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

            print("not valid form")
            return render(request, "members/set/set_password.html", {'form': form })
    else:
        form = SetPasswordForm()
        print("request method != POST")

    return render(request, "members/set/set_password.html", {'form': form })

def login(request):
    form = LoginForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            entered_username = form.cleaned_data.get('username')
            entered_password = form.cleaned_data.get('password')

            # if user exists
            if Passwords.objects.filter(username=entered_username).exists():

                # check password
                member = Passwords.objects.get(username=entered_username)
                password = member.password
                print(entered_password, password)

                # if password is correct
                if check_password(entered_password, password):
                    print("logged in")
                    return render(request, "members/home/index.html", {'form': form})
                else:
                    print("wrong password")
                    messages.info(request, "Wrong Password")
                    return render(request, "members/home/login.html", {'form': form})

            else:
                print("no members")
                messages.info(request, "You are not a member")
                return render(request, "members/home/login.html", {'form': form})


    return render(request, "members/home/login.html", { 'form': form })
