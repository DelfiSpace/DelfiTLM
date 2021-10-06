"""Apps config file"""
from django.apps import AppConfig

# pylint: disable=all
class AppConfig(AppConfig):
    """App config class"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
