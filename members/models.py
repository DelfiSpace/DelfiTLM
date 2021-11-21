import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager

# class User(AbstractUser):
#
#     def __str__(self):
#         return self.email
#
# class MyUserManager(BaseUserManager):
#     def create_user(self, username, password=None):
#
#         user = self.model(
#             username=username,
#         )
#
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, username, password=None):
#         """
#         Creates and saves a superuser with the given email, date of
#         birth and password.
#         """
#         user = self.create_user(
#             username,
#             password=password,
#         )
#         user.is_admin = True
#         user.save(using=self._db)
#         return user
#
#
# class Member(AbstractBaseUser):
#     UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     username = models.CharField(max_length=70, unique=True)
#     email = models.CharField(max_length=320, null=False, blank=False)
#     password = models.CharField(max_length=120,
#                                 validators=[
#                                     RegexValidator(regex='^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
#                                                    message='Enter password containing min 8 characters, min 1 upper and lower case letter, 1 number and 1 special character')
#                                 ], null=True, blank=True)
#     role = models.CharField(max_length=60, null=True, blank=True)
#     created_at = models.DateField(null=True, blank=True)
#     active = models.BooleanField(null=True, blank=True)
#     last_changed = models.DateField(null=True, blank=True)
#     last_login = models.TimeField(null=True, blank=True)
#
#     objects = MyUserManager()
#
#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = ['password',]
#
#     def __str__(self):
#         return self.email
#
#     def has_perm(self, perm, obj=None):
#         "Does the user have a specific permission?"
#         # Simplest possible answer: Yes, always
#         return True
#
#     def has_module_perms(self, app_label):
#         "Does the user have permissions to view the app `app_label`?"
#         # Simplest possible answer: Yes, always
#         return True
#
#     @property
#     def is_staff(self):
#         "Is the user a member of staff?"
#         # Simplest possible answer: All admins are staff
#         return self.is_admin
#
#
# class Admin(BaseUserManager):
#     def create_user(self, username, password=None):
#         if not username:
#             raise ValueError("Users must have an username")
#
#         user = self.model(
#             username=username,
#         )
#
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, username, password):
#         user = self.create_user(
#             password=password,
#             username=username,
#         )
#         user.is_admin = True
#         user.is_staff = True
#         user.is_superuser = True
#         user.save(using=self._db)
#         return user

class Member(AbstractUser):
    UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=70, unique=True)
    email = models.CharField(max_length=320, unique=True, null=False, blank=False)
    password = models.CharField(max_length=120,
                                validators=[
                                    RegexValidator(regex='^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                                                   message='Enter password containing min 8 characters, min 1 upper and lower case letter, 1 number and 1 special character')
                                ], null=True, blank=True)
    role = models.CharField(max_length=60, null=True, blank=True)
    created_at = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=False, null=False, blank=False)
    last_changed = models.DateField(null=True, blank=True)
    last_login = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.username
