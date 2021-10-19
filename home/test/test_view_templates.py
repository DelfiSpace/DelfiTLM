"""Test views html templates"""
from django.test import SimpleTestCase, Client
from django.urls import reverse


# pylint: disable=all

class TestViews(SimpleTestCase):

    def test_index(self):
        self.client = Client()
        self.list_url = reverse('homepage')
        response = self.client.get(self.list_url)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')