"""authentication_backend"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from ..models import Member


class AuthenticationBackend(BaseBackend):
    """Custom authentication backend"""

    def authenticate(self, username=None, password=None):
        """Authentication method"""

        if Member.objects.filter(username=username).exists():
            # check password
            member = Member.objects.get(username=username)
            password_found = member.password

            # if password is correct
            if check_password(password, password_found):
                return Member.objects.get(username=username)

        return None

    def get_user(self, user_id):
        try:
            return Member.objects.get(pk=user_id)
        except Member.DoesNotExist:
            return None
