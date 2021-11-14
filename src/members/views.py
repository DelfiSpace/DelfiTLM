"""API request handling. Map requests to the corresponding HTMLs."""
from django.shortcuts import render
from .forms import SetPasswordForm
from .models import Members, Passwords
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.utils import timezone

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
            # entered_confirmpassword = form.cleaned_data['confirm_password']

            if Members.objects.filter(username=entered_username).exists():

                if Passwords.objects.filter(username=entered_username).exists():
                    print("password exists, need to make change password page")
                    return render(request, "members/home/index.html")
                password = form.save(commit=False)
                member = Members.objects.get(username=entered_username)
                password.member_id_id = member.UUID
                password.UUID = member.UUID
                password.username = entered_username
                password.password = entered_password
                password.last_chaged = timezone.now()
                password.save()
                return render(request, "members/home/index.html")

            else:
                print("user not found")
        else:
            form.errors
            print("not valid form")
    else:
        form = SetPasswordForm()
        print("request method != POST")

    return render(request, "members/set/index.html", {'form': form })