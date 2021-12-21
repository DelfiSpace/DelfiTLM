"""authentication_backend"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from ..models import Member


class AuthenticationBackend(ModelBackend):
    """Custom authentication backend"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authentication method"""

        if Member.objects.filter(username=username).exists():
            # check password
            member = Member.objects.get(username=username)
            password_found = member.password

            # logins from blocked users
            if member.is_active is False:
                return None

            # if password is correct
            if check_password(password, password_found):
                return Member.objects.get(username=username)

        return None

    def get_user(self, user_id):
        try:
            return Member.objects.get(pk=user_id)
        except Member.DoesNotExist:
            return None
