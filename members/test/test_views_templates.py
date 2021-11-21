"""Test views html templates"""
from django.test import SimpleTestCase, Client, TestCase
from django.urls import reverse
from django.test.client import Client
from ..models import Member
# import unittest
# from django.contrib.auth.models import User

# pylint: disable=all

class TestViews(SimpleTestCase):

    def test_index(self):
        self.client = Client()
        self.list_url = reverse('ewilgs_home')
        response = self.client.get(self.list_url)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ewilgs/home/index.html')

class LoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user("test", "test@email,com", "testpassword")

    def testLogin(self):
        self.client.login(user='test', password='testpassword')
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

class HomeTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Member.objects.create_user("test", "test@email,com", "testpassword")

    def userLoggedIn(self):
        self.client.login(user='test', password='testpassword')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)

    def userNotLoggedIn(self):
        # self.client.login(user='test', password='testpassword')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 400)

class SetPasswordTestCase(TestCase):
    def SetTestCase(self):
        # self.client.login(user='test', password='testpassword')
        response = self.client.get(reverse('set'))
        self.assertEqual(response.status_code, 200)

class ChangePasswordTestCase(TestCase):
    def ChangeTestCase(self):
        # self.client.login(user='test', password='testpassword')
        response = self.client.get(reverse('change'))
        self.assertEqual(response.status_code, 200)

