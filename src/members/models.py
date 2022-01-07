"""Database model for this app"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
# from rest_framework_api_key.models import AbstractAPIKey
# import string
# import random

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


# class APIKey(AbstractAPIKey):
#     member = models.ForeignKey(
#         Member,
#         on_delete=models.CASCADE,
#         to_field="username",
#         related_name="api_keys",
#     )


# class APIKey(models.Model):

#     user = models.ForeignKey(Member, to_field="username",
#                               db_column="radio_amateur",
#                               null=False, on_delete=models.CASCADE)
#     key = models.CharField(max_length=40, blank=True)

#     def __unicode__(self):
#         return "%s: %s" % (self.user, self.key)

#     def save(self, *args, **kwargs):
#         if not self.key:
#             self.key = KeyGenerator.create_key()

#         super(APIKey, self).save(*args, **kwargs)
