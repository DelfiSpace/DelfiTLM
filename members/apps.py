"""Apps config file"""
from django.apps import AppConfig

# pylint: disable=all
class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'members'
