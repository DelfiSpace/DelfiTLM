"""API request handling. Map requests to the corresponding HTMLs."""
import json
from django.http.response import JsonResponse
from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from .forms import RegisterForm, LoginForm, ChangePasswordForm
from .models import APIKey, Member


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
            current_site = get_current_site(request)

            message = render_to_string('members/set/register_email_verification.html', {
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
            messages.info(request, "Please confirm your email address to complete the registration")
            return redirect("homepage")

        messages.error(request, "Unsuccessful registration")

    return render(request, "members/set/register.html", {'form': form})

def activate(request, uidb64, token):
    """Activate user email"""
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
        messages.info(request, "Thank you for your email confirmation. \
                            Now you can login into your account.")
    else:
        messages.error(request, 'Activation link is invalid!')
    return render(request, "home/index.html")


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
                messages.error(request, "Email not verified")
                return render(request, "members/home/login.html", {'form': form})

            if member is not None and member.is_active is True:
                login(request, member)
                Member.objects.filter(username=member.username).update(
                        last_login=timezone.now()
                    )
                return render(request, "members/home/profile.html")

        messages.error(request, "Invalid username or password")

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
            messages.info(request, "Password has been changed successfully")
            return redirect('profile')

        messages.error(request, "Invalid password")

    return render(request, "members/set/change_password.html", {'form': form })
