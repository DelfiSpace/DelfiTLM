from django.test import TestCase
from ..models import Member

class MemberModelTestCase(TestCase):

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
        # Members.objects.create(name="userA", email="user@email.com", role="userRole", created_at="10/22/21", active=True)

    def test_members(self):
        userA = Member.objects.get(name="userA")
        self.assertEqual(userA.email, "user@email.com")