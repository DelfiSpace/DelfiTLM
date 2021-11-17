from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from ..models import Passwords

class AuthenticationBackend(BaseBackend):

    def authenticate(self, username=None, password=None):
        print("authentication called")
        if Passwords.objects.filter(username=username).exists():
            # check password
            member = Passwords.objects.get(username=username)
            passwordFound = member.password
            # print(entered_password, password)

            # if password is correct
            if check_password(password, passwordFound):
                return member
            return None

    def get_user(self, user_id):
        try:
            return Passwords.objects.get(pk=user_id)
        except Passwords.DoesNotExist:
            return None