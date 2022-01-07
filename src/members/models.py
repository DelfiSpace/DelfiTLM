"""Database model for this app"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework_api_key.models import AbstractAPIKey

class Member(AbstractUser):
    """Extended custom user from User"""

    UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=191, unique=True)
    email = models.EmailField(max_length=320, unique=True, null=False, blank=False)
    password = models.CharField(max_length=120, null=False, blank=False)
    role = models.CharField(max_length=60, default="radio_amateur")
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(null=True, blank=True)
    last_changed = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username


class APIKey(AbstractAPIKey):
    username = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        to_field="username",
        db_column="username",
        related_name="api_keys",
    )
