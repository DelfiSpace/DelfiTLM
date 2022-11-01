"""Test views html templates"""

from transmission.models import Downlink, Satellite, Uplink
from transmission.processing.save_raw_data import store_frame
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.test.client import Client
from ..models import Member
import re
import django
import time

# pylint: disable=all


class TestLogin(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com',verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()

        self.user = Member.objects.create_user(username='user1', email='user1@email.com',verified=True)
        self.user.set_password('delfispace')
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_login(self):
        # login form retrieved
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        # login request successful
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')

    def test_login_with_email(self):
        # login form retrieved
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        # login request successful
        response = self.client.post(reverse('login'), {'username': 'user@email.com', 'password': 'delfispace4242'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')

    def test_logout(self):
        # login form retrieved
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

        # login request successful
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')

        # logout request successful, redirect to homepage
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')

    def test_login_wrong_credentials(self):
        # login form retrieved
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

        # empty username field
        response = self.client.post(reverse('login'), {'username': '', 'password': 'delfispace4242'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password!')
        self.assertTemplateUsed(response, 'registration/login.html')

        # empty password field
        response = self.client.post(reverse('login'), {'username': 'user', 'password': ''})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password!')
        self.assertTemplateUsed(response, 'registration/login.html')

        # wrong username
        response = self.client.post(reverse('login'), {'username': 'admin', 'password': 'delfispace4242'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password!')
        self.assertTemplateUsed(response, 'registration/login.html')

        # wrong email
        response = self.client.post(reverse('login'), {'username': 'user1@email.com', 'password': 'delfispace4242'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password!')
        self.assertTemplateUsed(response, 'registration/login.html')

        # wrong password
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace424'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password!')
        self.assertTemplateUsed(response, 'registration/login.html')

        # wrong username and password
        response = self.client.post(reverse('login'), {'username': 'user1', 'password': 'delfispace424'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password!')
        self.assertTemplateUsed(response, 'registration/login.html')


class TestAccount(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='test@email.com')
        self.user.set_password('delfispace4242')
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_user_logged_in(self):
        # the user is logged in and can view the account page
        login = self.client.login(username='user', password='delfispace4242')
        self.assertTrue(login)
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')

    def test_user_not_logged_in(self):
        # the user is not logged in and since account is login protected the user is redirected to login
        response = self.client.get(reverse('account'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')


class TestRegister(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_register(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_register_post_request(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

        response = self.client.post(reverse('register'), {'username': 'user2',
                                                          'email': 'test2@email.com',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace4242'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html') #when creating an account we receive an e-mail for verification

    def test_register_resend_verification(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

        response = self.client.post(reverse('register'), {'username': 'user2',
                                                          'email': 'test2@email.com',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace4242'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')

        # login attempt with unverified emil
        response = self.client.post(reverse('login'), {'username': 'user2', 'password': 'delfispace4242'},follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/resend_verification_email.html')
        # resend verification email
        response = self.client.post(reverse('resend_verify'), {'email': 'test2@email.com'}, follow=True)
        # redirect to login page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')


    def test_register_email_resend_verification_bad_weather(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

        response = self.client.post(reverse('register'), {'username': 'user2',
                                                          'email': 'test2@email.com',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace4242'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')

        response = self.client.post(reverse('login'), {'username': 'user2', 'password': 'delfispace4242'},follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/resend_verification_email.html')

        # request verification using an already verified email from the system
        response = self.client.post(reverse('resend_verify'), {'email': 'user@email.com'}, follow=True)

        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'registration/resend_verification_email.html')

        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Email is unknown or is already verified!')

        # request verification using an unknown email
        response = self.client.post(reverse('resend_verify'), {'email': 'foo@email.com'}, follow=True)
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'registration/resend_verification_email.html')

        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Email is unknown or is already verified!')

    def test_register_user_already_exists(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

        response = self.client.post(reverse('register'), {'username': 'user',
                                                          'email': 'test@email.com',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace4242'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Unsuccessful registration')
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_register_invalid_email(self):
        # register form successfully retrieved
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
        # bad email
        response = self.client.post(reverse('register'), {'username': 'user3',
                                                          'email': 'test',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace4242'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'registration/register.html')

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
        self.assertTemplateUsed(response, 'registration/register.html')

        # password too short
        response = self.client.post(reverse('register'), {'username': 'user3',
                                                          'email': 'test3@email.com',
                                                          'password1': 'short',
                                                          'password2': 'short'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'registration/register.html')

        # password same as username
        response = self.client.post(reverse('register'), {'username': 'qwertyuser',
                                                          'email': 'test3@email.com',
                                                          'password1': 'qwertyuser',
                                                          'password2': 'qwertyuser'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'registration/register.html')

        # password mismatch
        response = self.client.post(reverse('register'), {'username': 'user3',
                                                          'email': 'test3@email.com',
                                                          'password1': 'delfispace4242',
                                                          'password2': 'delfispace424'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'registration/register.html')


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
        # the user is redirected to the login page
        response = self.client.get(reverse('change_password'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_change_password_user_logged_in(self):
        # user is logged in and password reset is login protected
        # the user receives the change password form
        self.client.login(username='user', password='delfispace4242')
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/change_password.html')

    def test_password_changed(self):
        # user is logged in and password reset is login protected
        # the user receives the change django password form
        self.client.login(username='user', password='delfispace4242')
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/change_password.html')

        response = self.client.post(reverse('change_password'), {
                                                          'old_password': 'delfispace4242',
                                                          'new_password1': 'delfispace424',
                                                          'new_password2': 'delfispace424'}, follow=True)

        # redirected to the account page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')

    def test_change_invalid_password(self):
        # reset password form successfully retrieved
        self.client.login(username='user', password='delfispace4242')
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/change_password.html')

        # password only numeric
        response = self.client.post(reverse('change_password'), {
                                                          'old_password': 'delfispace4242',
                                                          'new_password1': '1155239711568432464',
                                                          'new_password2': '1155239711568432464'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'registration/change_password.html')

        # password too short
        response = self.client.post(reverse('change_password'), {
                                                          'old_password': 'delfispace4242',
                                                          'new_password1': 'short',
                                                          'new_password2': 'short'})
        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'registration/change_password.html')

        # new password mismatch
        response = self.client.post(reverse('change_password'), {
                                                           'old_password': 'delfispace4242',
                                                          'new_password1': 'delfispace443',
                                                          'new_password2': 'delfispace4343'})

        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertTemplateUsed(response, 'registration/change_password.html')


class TestAccountVerification(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_login(self):
        # login form retrieved
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 302)

        self.user.verified = True #the user verified the account
        self.user.save()
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')  # account is verified so we proceed to account page

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
        # activate/
        token_regex = r"activate\/([A-Za-z0-9:\-]+)/([A-Za-z0-9:\-]+)"
        email_content = django.core.mail.outbox[1].body # get the second email since the first is the welcome email
        match = re.search(token_regex, email_content)

        uid = match.group(1)
        token = match.group(2)

        response = self.client.post(reverse('activate', args=[uid, token]))
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Please confirm your email address to complete the registration.')

        self.assertEqual(response.status_code, 200)

        # Invalid link
        uid = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        token = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

        response = self.client.post(reverse('activate', args=[uid, token]))
        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)
        self.assertEqual(str(messages[0]), 'Verification link is invalid or expired!')
        self.assertEqual(response.status_code, 400)

    def test_reset_password(self):
        payload = {
            'email': 'user@email.com'
        }
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_form.html')

        response = self.client.post(reverse('password_reset'), payload)
        self.assertEqual(response.status_code, 302)

        # Get token from email
        token_regex = r"reset\/([A-Za-z0-9:\-]+)/([A-Za-z0-9:\-]+)"
        email_content = django.core.mail.outbox[0].body
        match = re.search(token_regex, email_content)

        uid = match.group(1)
        token = match.group(2)

        payload = {
            'new_password1': 'delfispace',
            'new_password2': 'delfispace'
        }

        response = self.client.post(reverse('password_reset_confirm', args=[uid, token]), payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace'})
        self.assertEqual(response.status_code, 401)
        messages = list(response.context['messages'])
        self.assertNotEqual(str(messages[0]), 'Invalid username or password!')


    def test_reset_password_unregistered_email(self):
        payload = {
            'email': 'unknown_user@email.com'
        }
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_form.html')

        response = self.client.post(reverse('password_reset'), payload)
        messages = list(response.context['messages'])
        self.assertTrue(len(messages)>0)

        self.assertEqual(str(messages[0]), 'Invalid email address')

    def test_reset_password_bad_token(self):
        payload = {
            'email': 'user@email.com'
        }
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_form.html')

        response = self.client.post(reverse('password_reset'), payload)
        self.assertEqual(response.status_code, 302)

        # Get token from email

        uid = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        token = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

        payload = {
            'new_password1': 'delfispace',
            'new_password2': 'delfispace'
        }
        response = self.client.post(reverse('password_reset_confirm', args=[uid, token]), payload)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Invalid username or password!')


class TestAccountDeletion(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.add_downlink_permission = Permission.objects.get(codename='add_downlink')
        self.add_uplink_permission = Permission.objects.get(codename='add_uplink')
        self.user.user_permissions.add(self.add_downlink_permission)
        self.user.user_permissions.add(self.add_uplink_permission)
        self.user.save()

        self.admin_user = Member.objects.create_superuser(username='admin', email='admin@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()

        Satellite.objects.create(sat='delfipq', norad_id=1).save()

        # add 3 valid frames from delfi_pq
        f1 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F00008730150020002008100400000002D63007DE95A02FF64FFF1FFFF000F0BC3004411B00F990F8A000E03ECFFB3FFC300000000000000240000000000000EB80014FFFF0021000010CD0FE111560EECFF7CFEE0FF65FF0F00080000001000000FA20146104D012C00100000000500000B0001460B3B"}
        f2 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F000081B015002000300000000000000000000000000000000000000000000"}
        f3 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F000082801500200040093000E00000000AB0078993702FFEDFC10250027FFDDFF8D011A000000000000FFB4"}

        for f in [f1, f2, f3]:
            store_frame(f, "uplink", "user")
            store_frame(f, "downlink", "user")

    def test_delete_account_operator(self):
        # operators and superusers cannot delete their accounts by themselves
        # when not logged in redirect to login
        response = self.client.get(reverse('delete_account'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

        # login
        self.client.post(reverse('login'), {'username': 'admin', 'password': 'delfispace4242'})
        # get delete form
        response = self.client.get(reverse('delete_account'))
        self.assertEqual(response.status_code, 302)

        self.client.post(reverse('delete_account'), {'username': 'user', 'password': 'delfispace4242', 'challenge': 'delete my account'})

        self.assertEqual(Member.objects.filter(username='admin').exists(), True)
        self.assertEqual(len(django.core.mail.outbox), 0)

    def test_delete_account(self):
        # when not logged in redirect to login
        response = self.client.get(reverse('delete_account'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

        # login
        self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        # get delete form
        response = self.client.get(reverse('delete_account'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/delete_account_form.html')

        self.client.post(reverse('delete_account'), {'username': 'user', 'password': 'delfispace4242', 'challenge': 'delete my account'})

        self.assertEqual(Member.objects.filter(username='user').exists(), False)
        self.assertEqual(len(django.core.mail.outbox), 1)

    def test_delete_account_bad_form(self):
        # login
        self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        # get delete form
        response = self.client.get(reverse('delete_account'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/delete_account_form.html')

        # wrong username
        response = self.client.post(reverse('delete_account'), {'username': 'user1', 'password': 'delfispace4242', 'challenge': 'delete my account'})
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'registration/delete_account_form.html')

        # wrong password
        response = self.client.post(reverse('delete_account'), {'username': 'user', 'password': 'delfispace', 'challenge': 'delete my account'})
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'registration/delete_account_form.html')

        # wrong challenge
        response = self.client.post(reverse('delete_account'), {'username': 'user', 'password': 'delfispace', 'challenge': 'delete'})
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'registration/delete_account_form.html')

        # user still exists, no emails have been sent
        self.assertEqual(Member.objects.filter(username='user').exists(), True)
        self.assertEqual(len(django.core.mail.outbox), 0)


    def test_telemetry_persistence_after_account_deletion(self):
        # check number of frames
        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)

        for frame in Downlink.objects.all():
            self.assertEquals(frame.observer, str(self.user.UUID))

        for frame in Uplink.objects.all():
            self.assertEquals(frame.operator, 'user')

        # login
        self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        # get delete form
        response = self.client.get(reverse('delete_account'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/delete_account_form.html')

        self.client.post(reverse('delete_account'), {'username': 'user', 'password': 'delfispace4242', 'challenge': 'delete my account'})

        self.assertEqual(Member.objects.filter(username='user').exists(), False)
        self.assertEqual(len(django.core.mail.outbox), 1)

        # check number of frames
        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)

        for frame in Downlink.objects.all():
            self.assertEquals(frame.observer, str(self.user.UUID))

        for frame in Uplink.objects.all():
            self.assertEquals(frame.operator, 'user')


class TestEmailChangeRequest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()
        # add a second user
        self.user = Member.objects.create_user(username='user2', email='user2@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()

    def test_change_email(self):
        # login
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'}, follow=True)
        self.assertEqual(response.status_code, 200)
        # request email change
        response = self.client.get(reverse('change_email'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('change_email'), {'email': 'superuser@email.com', 'email_confirm': 'superuser@email.com'})
        self.assertEqual(response.status_code, 302)
        # check if new email gets updated
        user = Member.objects.get(username='user')
        self.assertEqual(user.email, "user@email.com")
        self.assertEqual(user.new_email, "superuser@email.com")

        # verify new email
        token_regex = r"activate\/([A-Za-z0-9:\-]+)/([A-Za-z0-9:\-]+)"
        email_content = django.core.mail.outbox[1].body
        match = re.search(token_regex, email_content)

        uid = match.group(1)
        token = match.group(2)

        response = self.client.post(reverse('activate', args=[uid, token]))
        self.assertEqual(response.status_code, 200)

        # check if update was successful
        user = Member.objects.get(username='user')
        self.assertEqual(user.email, "superuser@email.com")
        self.assertEqual(user.new_email, None)

    def test_change_email_duplicate_requests(self):
        # login
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'}, follow=True)
        self.assertEqual(response.status_code, 200)
        # request email change
        response = self.client.get(reverse('change_email'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('change_email'), {'email': 'superuser@email.com', 'email_confirm': 'superuser@email.com'})
        self.assertEqual(response.status_code, 302)
        # check if new email gets updated
        user = Member.objects.get(username='user')
        self.assertEqual(user.email, "user@email.com")
        self.assertEqual(user.new_email, "superuser@email.com")

        time.sleep(1)

        # make a duplicate request with a different email address
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('change_email'), {'email': 'superuser2@email.com', 'email_confirm': 'superuser2@email.com'})
        self.assertEqual(response.status_code, 302)

        # check if new email gets updated
        user = Member.objects.get(username='user')
        self.assertEqual(user.email, "user@email.com")
        self.assertEqual(user.new_email, "superuser2@email.com")

        # # verify new email
        token_regex = r"activate\/([A-Za-z0-9:\-]+)/([A-Za-z0-9:\-]+)"
        email_content = django.core.mail.outbox[1].body
        match = re.search(token_regex, email_content)

        uid = match.group(1)
        token = match.group(2)

        # first link verification fails
        response = self.client.post(reverse('activate', args=[uid, token]))
        self.assertEqual(response.status_code, 400)
        # new email is set to the most recently requested update
        user = Member.objects.get(username='user')
        self.assertEqual(user.email, "user@email.com")
        self.assertEqual(user.new_email, "superuser2@email.com")

        # most recent link successfully verifies the new email
        token_regex = r"activate\/([A-Za-z0-9:\-]+)/([A-Za-z0-9:\-]+)"
        email_content = django.core.mail.outbox[3].body
        match = re.search(token_regex, email_content)

        uid = match.group(1)
        token = match.group(2)
        # second link verification succeeds
        response = self.client.post(reverse('activate', args=[uid, token]))
        self.assertEqual(response.status_code, 200)

        # check if update was successful
        user = Member.objects.get(username='user')
        self.assertEqual(user.email, "superuser2@email.com")
        self.assertEqual(user.new_email, None)

    def test_change_email_bad_weather(self):

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'}, follow=True)
        self.assertEqual(response.status_code, 200)

        # emails don't match
        response = self.client.post(reverse('change_email'), {'email': 'superuser1@email.com', 'email_confirm': 'superuser@email.com'})
        self.assertEqual(response.status_code, 400)

        user = Member.objects.get(username='user')
        self.assertEqual(user.email, "user@email.com")
        self.assertEqual(user.new_email, None)

        # email is the same as the current email
        response = self.client.post(reverse('change_email'), {'email': 'user@email.com', 'email_confirm': 'user@email.com'})
        self.assertEqual(response.status_code, 400)

        user = Member.objects.get(username='user')
        self.assertEqual(user.email, "user@email.com")
        self.assertEqual(user.new_email, None)

        # email is register at another account
        response = self.client.post(reverse('change_email'), {'email': 'user2@email.com', 'email_confirm': 'user2@email.com'})
        self.assertEqual(response.status_code, 400)

        user = Member.objects.get(username='user')
        self.assertEqual(user.email, "user@email.com")
        self.assertEqual(user.new_email, None)
