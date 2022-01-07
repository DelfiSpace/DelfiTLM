"""admin.py"""
from django.contrib import admin
from .models import Member
from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin
from .models import APIKey

@admin.register(APIKey)
class APIKeyModelAdmin(APIKeyModelAdmin):
    pass

admin.site.register(Member)
