from django.db import models
from .forms import SetPasswordForm

# Create your models here.

class Members(models.Model):
    username = models.CharField(max_length=70, unique=True)
    email = models.CharField(max_length=320, unique=True)
    role = models.CharField(max_length=60)
    created_at = models.DateField(null=True)
    active = models.BooleanField(null=True)

    def __str__(self):
        return self.username

class Passwords(models.Model):
    member_id = models.ForeignKey(Members, on_delete=models.CASCADE)
    username = models.CharField(max_length=70, unique=True)
    password = models.CharField(max_length=120)
    last_changed = models.DateField(null=True)

    def __str__(self):
        return self.username

    def save(self, commit=True):
        password = super(SetPasswordForm, self).save(commit=False)
        username, password = self.cleaned_data["username"].split()
        password.username = username
        password.password = password
        if commit:
            password.save()
        return password