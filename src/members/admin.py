"""Admin page for managing the database models"""

# Register your models here.

from django.contrib import admin
from .models import Members, Passwords

admin.site.register(Members)
admin.site.register(Passwords)