"""Database model for this app"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class Member(AbstractUser):
    """Extended custom user from User"""

    UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=70, unique=True)
    email = models.CharField(max_length=320, unique=True, null=False, blank=False)
    password = models.CharField(max_length=120, null=True, blank=True)
    role = models.CharField(max_length=60, default="radio_amateur")
    created_at = models.DateField(null=True, blank=True)
    last_changed = models.DateField(null=True, blank=True)
    last_login = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.username
