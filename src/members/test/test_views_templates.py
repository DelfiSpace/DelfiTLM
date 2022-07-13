"""Test views html templates"""
from django.test import SimpleTestCase, Client, TestCase
from django.urls import reverse
from django.test.client import Client
from ..models import Member
import re
import django
# import unittest
# from django.contrib.auth.models import User

# pylint: disable=all

class TestLogin(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com',verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_login(self):
        # login form retrieved
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/home/login.html')
        # login request successful
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/home/profile.html')

    def test_logout(self):
        # login form retrieved
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/home/login.html')

        # login request successful
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/home/profile.html')

        # logout request successful, redirect to homepage
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


    def test_login_wrong_credentials(self):
        # login form retrieved
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

        # empty username field
        response = self.client.post(reverse('login'), {'username': '', 'password': 'delfispace4242'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password')
        self.assertTemplateUsed(response, 'members/home/login.html')

        # empty password field
        response = self.client.post(reverse('login'), {'username': 'user', 'password': ''})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password')
        self.assertTemplateUsed(response, 'members/home/login.html')

        # wrong username
        response = self.client.post(reverse('login'), {'username': 'admin', 'password': 'delfispace4242'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password')
        self.assertTemplateUsed(response, 'members/home/login.html')

        # wrong password
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace424'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password')
        self.assertTemplateUsed(response, 'members/home/login.html')

        # wrong username and password
        response = self.client.post(reverse('login'), {'username': 'user1', 'password': 'delfispace424'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password')
        self.assertTemplateUsed(response, 'members/home/login.html')

class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='test@email.com')
        self.user.set_password('delfispace4242')
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_user_logged_in(self):
        # the user is logged in and can view the profile page
        login = self.client.login(username='user', password='delfispace4242')
        self.assertTrue(login)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/home/profile.html')

    def test_user_not_logged_in(self):
        # the user is not logged in and since profile is login protected the user is redirected to login
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

class TestRegister(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com')
        self.user.set_password('delfispace4242')
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_register(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/set/register.html')

    def test_register_post_request(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/set/register.html')

        response = self.client.post(reverse('register'), {'username': 'user2',
                                                          'email': 'test2@email.com',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace4242'})
        self.assertEqual(response.status_code, 302)
        # self.assertTemplateUsed(response, 'members/home/profile.html')
        self.assertTemplateUsed(response, 'members/set/register_email_verification.html') #when creating an account we receive an e-mail for verification

    def test_register_user_already_exists(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/set/register.html')

        response = self.client.post(reverse('register'), {'username': 'user',
                                                          'email': 'test@email.com',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace4242'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Unsuccessful registration')
        self.assertTemplateUsed(response, 'members/set/register.html')

    def test_register_invalid_email(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/set/register.html')
        # bad email
        response = self.client.post(reverse('register'), {'username': 'user3',
                                                          'email': 'test',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace4242'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'members/set/register.html')

    def test_register_invalid_password(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

        # password only numeric
        response = self.client.post(reverse('register'), {'username': 'user3',
                                                          'email': 'test3@email.com',
                                                          'password1': '1155239711568432464',
                                                          'password2': '1155239711568432464'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'members/set/register.html')

        # password too short
        response = self.client.post(reverse('register'), {'username': 'user3',
                                                          'email': 'test3@email.com',
                                                          'password1': 'short',
                                                          'password2': 'short'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'members/set/register.html')

        # password same as username
        response = self.client.post(reverse('register'), {'username': 'qwertyuser',
                                                          'email': 'test3@email.com',
                                                          'password1': 'qwertyuser',
                                                          'password2': 'qwertyuser'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'members/set/register.html')

        # password missmatch
        response = self.client.post(reverse('register'), {'username': 'user3',
                                                          'email': 'test3@email.com',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace424'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'members/set/register.html')


class TestChangePassword(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='test@email.com')
        self.user.set_password('delfispace4242')
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_change_password_user_not_logged_in(self):
        # user is not logged in and password reset is login protected
        # the user is redirected to the home page
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 302)

    def test_change_password_user_logged_in(self):
        # user is logged in and password reset is login protected
        # the user receives the change password form
        self.client.login(username='user', password='delfispace4242')
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/set/change_password.html')


    def test_password_changed(self):
        # user is logged in and password reset is login protected
        # the user receives the changedjango password form
        self.client.login(username='user', password='delfispace4242')
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/set/change_password.html')


        response = self.client.post(reverse('change_password'), {
                                                          'old_password': 'delfispace4242',
                                                          'new_password1': 'delfispace424',
                                                          'new_password2': 'delfispace424'})

        # redirected to the profile page
        self.assertEqual(response.status_code, 302)

    def test_change_invalid_password(self):
        # reset password form successfully retrieved
        self.client.login(username='user', password='delfispace4242')
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/set/change_password.html')


        # password only numeric
        response = self.client.post(reverse('change_password'), {
                                                          'old_password': 'delfispace4242',
                                                          'new_password1': '1155239711568432464',
                                                          'new_password2': '1155239711568432464'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'members/set/change_password.html')


        # password too short
        response = self.client.post(reverse('change_password'), {
                                                          'old_password': 'delfispace4242',
                                                          'new_password1': 'short',
                                                          'new_password2': 'short'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'members/set/change_password.html')


        # new password missmatch
        response = self.client.post(reverse('change_password'), {
                                                           'old_password': 'delfispace4242',
                                                          'new_password1': 'delfispace443',
                                                          'new_password2': 'delfispace4343'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'members/set/change_password.html')

class TestAccountVerification(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com')
        self.user.set_password('delfispace4242')
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_login(self):
        # login form retrieved
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/home/login.html')

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/home/login.html') #account is not verified so we return to login

        self.user.verified = True #the user verified the account
        self.user.save()
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/home/profile.html')  # account is verified so we proceed to profile page

    def test_verify_email(self):
        # Verify email address
        username = 'userTest'
        payload = {
            'email': 'test@example.com',
            'password1': 'TestpassUltra1',
            'password2': 'TestpassUltra1',
            'username': username,
        }
        response = self.client.post(reverse('register'), payload)
        self.assertEqual(response.status_code, 302)

        # Get token from email
        # members/activate/
        token_regex = r"members\/activate\/([A-Za-z0-9:\-]+)/([A-Za-z0-9:\-]+)"
        email_content = django.core.mail.outbox[0].body
        match = re.search(token_regex, email_content)

        uid = match.group(1)
        token = match.group(2)

        response = self.client.post(reverse('activate', args=[uid, token]))
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Please confirm your email address to complete the registration')

        self.assertEqual(response.status_code, 200)

        # Invalid link
        uid = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        token = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

        response = self.client.post(reverse('activate', args=[uid, token]))
        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertEqual(str(messages[0]), 'Activation link is invalid!')
        self.assertEqual(response.status_code, 200)

