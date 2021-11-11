import uuid
from django.db import models
from django.core.validators import RegexValidator

# Create your models here.

class Members(models.Model):
    UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=70)
    email = models.CharField(max_length=320, unique=True)
    role = models.CharField(max_length=60, null=True, blank=True)
    created_at = models.DateField(null=True, blank=True)
    active = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return self.username

class Passwords(models.Model):
    UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member_id = models.ForeignKey(Members, on_delete=models.CASCADE)
    username = models.CharField(max_length=70)
    password = models.CharField(max_length=120,
                                validators=[
                                    RegexValidator(regex='^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                                                   message='Enter password containing min 8 characters, min 1 upper and lower case letter, 1 number and 1 special character')
                                ])
    last_changed = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.username