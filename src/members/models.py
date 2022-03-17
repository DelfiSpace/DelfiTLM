"""Database model for this app"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework_api_key.models import AbstractAPIKey

class Member(AbstractUser):
    """Extended custom user from User"""

    RADIO_AMATEUR = 'radio_amateur'
    OPERATOR = 'operator'
    LICENSED_OPERATOR = 'licensed_operator'

    ROLE_CHOICES = (
          (RADIO_AMATEUR, 'radio_amateur'),         # can view and submit Downlink data
          (OPERATOR, 'operator'),                   # can view and submit Downlink data & can view Downlink data
          (LICENSED_OPERATOR, 'licensed_operator'), # can view and submit both Uplink and Downlink data
      )

    UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=191, unique=True)
    email = models.EmailField(max_length=320, unique=True, null=False, blank=False)
    password = models.CharField(max_length=120, null=False, blank=False)
    role = models.CharField(choices=ROLE_CHOICES, max_length=60, default="radio_amateur")
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(null=True, blank=True)
    last_changed = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    #by Default, when creating an use, the account is not verified
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class APIKey(AbstractAPIKey):
    """API keys table"""
    username = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        to_field="username",
        db_column="username",
        related_name="api_keys",
    )
