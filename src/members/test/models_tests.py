"""Test cases for models"""
from django.test import TestCase
from ..models import Member

class MemberModelTestCase(TestCase):
    """Member model test"""
    @classmethod
    def setUp(cls):
        cls.member = Member.objects.create(
            name="userA",
            email="user@email.com",
            password="testpassword",
            role="userRole",
            created_at="10/22/21",
            active=True
        )

    def test_members(self):
        """test member with mock member"""
        user_a = Member.objects.get(name="userA")
        self.assertEqual(user_a.email, "user@email.com")
