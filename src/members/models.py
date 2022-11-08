"""Database model for this app"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework_api_key.models import AbstractAPIKey

class Member(AbstractUser):
    """Extended custom user from User"""

    UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=32, unique=True)
    email = models.EmailField(max_length=254, unique=True, null=False, blank=False)
    password = models.CharField(max_length=128, null=False, blank=False)
    role = models.CharField(max_length=64, default="radio_amateur")
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(null=True, blank=True)
    last_changed = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    #by default, when creating an user, the account is not verified
    verified = models.BooleanField(default=False)

    def __str__(self):
        return str(self.username)


class APIKey(AbstractAPIKey):
    """API keys table"""
    username = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        to_field="username",
        db_column="username",
        related_name="api_keys",
    )
