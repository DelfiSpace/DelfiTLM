"""Custom command for initializing an admin user"""
from django.core.management.base import BaseCommand
from members.models import Member

class Command(BaseCommand):
    """Django command class"""

    def handle(self, *args, **options):
        """Create and store admin user"""
        if Member.objects.count() == 0:
            username = 'admin'
            email = 'admin@admin.com'
            password = 'adminpwd'
            print(f'Creating account for {username}, {email}')
            admin = Member.objects.create_superuser(email=email,
                                                    username=username,
                                                    password=password
                                                    )
            admin.is_active = True
            admin.is_admin = True
            admin.verified = True
            admin.save()
        else:
            print('Admin account already exists')
