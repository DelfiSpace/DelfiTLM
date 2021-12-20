# from django.test import TestCase
# from members.models import Members
#
# class MembersTestCase(TestCase):
#     def setUp(self):
#         Members.objects.create(name="userA", email="user@email.com", role="userRole", created_at="10/22/21", active=True)
#         Members.objects.create(name="userB", email="user@email.com", role="userRole", created_at="10/22/21", active=True)
#
#     def test_members(self):
#         userA = Members.objects.get(name="userA")
#         self.assertEqual(userA.email, "user@email.com")
