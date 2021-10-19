
"""Test urls"""
from django.test import TestCase
from django.test import SimpleTestCase
from django.urls import resolve, reverse
from delfipq.views import *


# pylint: disable=all

class TestUrls(SimpleTestCase):
    def test_index(self):
        url = reverse('delfipq_home')
        self.assertEquals(resolve(url).func, home)