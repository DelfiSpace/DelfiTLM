
"""Test urls"""
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from transmission.views import home


# pylint: disable=all

class TestUrls(SimpleTestCase):
    def test_index(self):
        url = reverse('home')
        self.assertEquals(resolve(url).func, home)
