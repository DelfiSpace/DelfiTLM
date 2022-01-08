"""admin.py"""
from django.contrib import admin
from .models import APIKey
from .models import Member


admin.site.register(APIKey)
admin.site.register(Member)
