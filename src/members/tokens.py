"""Token generator module, used for email verification and password reset"""
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class TokenGenerator(PasswordResetTokenGenerator):
    """Token Generator class"""
# https://medium.com/@frfahim/django-registration-with-confirmation-email-bb5da011e4ef
    def _make_hash_value(self, user, timestamp):
        """Create token hash"""
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )
account_activation_token = TokenGenerator()
