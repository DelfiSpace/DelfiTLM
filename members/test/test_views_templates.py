"""Test views html templates"""
from django.test import SimpleTestCase, Client, TestCase
from django.urls import reverse


# pylint: disable=all

class TestViews(SimpleTestCase):

    def test_index(self):
        self.client = Client()
        self.list_url = reverse('ewilgs_home')
        response = self.client.get(self.list_url)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ewilgs/home/index.html')

class TestCalls(TestCase):
    def test_call_home_page(self):
        self.client = Client()
        self.list_url = reverse('members_home')
        response = self.client.get(self.list_url)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/home/index.html')

