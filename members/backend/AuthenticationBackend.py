from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from ..models import Member

class AuthenticationBackend(BaseBackend):

    def authenticate(self, username=None, password=None):
        print("authentication called")
        if Member.objects.filter(username=username).exists():
            # check password
            member = Member.objects.get(username=username)
            passwordFound = member.password

            print(member)
            print(password)
            print(passwordFound)
            # if password is correct
            if check_password(password, passwordFound):
                return Member.objects.get(username=username)
            return None

    def get_user(self, user_id):
        try:
            return Member.objects.get(pk=user_id)
        except Member.DoesNotExist:
            return None