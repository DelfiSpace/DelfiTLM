"""admin.py"""
from django.contrib import admin
from .models import Member

<<<<<<< HEAD
# Register your models here.

from django.contrib import admin
from .models import Members, Passwords

admin.site.register(Members)
admin.site.register(Passwords)
=======
admin.site.register(Member)
>>>>>>> origin/main
