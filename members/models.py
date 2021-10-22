from django.db import models

# Create your models here.

class Members(models.Model):
    username = models.CharField(max_length=70, unique=True)
    email = models.CharField(max_length=320, unique=True)
    role = models.CharField(max_length=60)
    created_at = models.DateField(null=True)
    active = models.BooleanField(null=True)

class Passwords(models.Model):
    member_id = models.ForeignKey(Members, on_delete=models.CASCADE)
    username = models.CharField(max_length=70, unique=True)
    password = models.CharField(max_length=120)
