"""Test views html templates"""
import json
from django.test import SimpleTestCase, Client, TestCase, RequestFactory
from rest_framework.test import force_authenticate
from django.contrib.auth.models import Permission
from django.urls import reverse
from ewilgs.models import Downlink
from ewilgs.views import submit_frame

from members.models import Member
from members.views import generate_key


# pylint: disable=all

class TestViews(SimpleTestCase):

    def test_index(self):
        self.client = Client()
        self.list_url = reverse('home')
        response = self.client.get(self.list_url)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ewilgs/home/index.html')

class TestSubmitFrames(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com')
        self.user.set_password('delfispace4242')
        permission = Permission.objects.get(codename='add_downlink')
        self.user.user_permissions.add(permission)
        self.user.save()

    def tearDown(self):
        self.client.logout()

    def test_submit_no_timestamps(self):

        self.assertEqual(len(Downlink.objects.all()), 0) # downlink table empty

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 200)
        frame = '{ "qos": 98.6, "pass": "qwerty", "frequency": 2455.66, "processed": true, "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}'
        frame_json = json.loads(frame)

        request_key = self.factory.get(path='members/key/', content_type='application/json')

        user = Member.objects.get(username='user')
        force_authenticate(request_key, user=user)

        request_key.user = user
        response_key = generate_key(request_key).content

        request = self.factory.post(path='submit_frame', data=frame_json, content_type='application/json')
        request.user = user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']

        response = submit_frame(request)

        self.assertEquals(response.status_code, 500)
        self.assertEqual(len(Downlink.objects.all()), 0) # dowlink table has no entry


    def test_submit_with_timestamps(self):

        self.assertEqual(len(Downlink.objects.all()), 0) # downlink table empty

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 200)
        frame = '{ "qos": 98.6, "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66, "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}'

        frame_json = json.loads(frame)
        request_key = self.factory.get(path='members/key/', content_type='application/json')

        user = Member.objects.get(username='user')
        force_authenticate(request_key, user=user)

        request_key.user = user
        response_key = generate_key(request_key).content

        request = self.factory.post(path='submit_frame', data=frame_json, content_type='application/json')
        request.user = user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']

        response = submit_frame(request)

        self.assertEquals(response.status_code, 201)
        self.assertEqual(len(Downlink.objects.all()), 1) # dowlink table has 1 entry
        self.assertEqual(str(Downlink.objects.first().receive_time), "2021-12-19 02:20:14.959630+00:00")


    def test_submit_with_non_utc_timestamps(self):

        self.assertEqual(len(Downlink.objects.all()), 0) # downlink table empty

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 200)
        frame = '{ "qos": 98.6, "timestamp": "2022-02-06 17:49:05.421398+01:00", "frequency": 2455.66, "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}'

        frame_json = json.loads(frame)
        request_key = self.factory.get(path='members/key/', content_type='application/json')

        user = Member.objects.get(username='user')
        force_authenticate(request_key, user=user)

        request_key.user = user
        response_key = generate_key(request_key).content

        request = self.factory.post(path='submit_frame', data=frame_json, content_type='application/json')
        request.user = user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']

        response = submit_frame(request)

        self.assertEquals(response.status_code, 201)
        self.assertEqual(len(Downlink.objects.all()), 1) # dowlink table has 1 entry
        self.assertEqual(str(Downlink.objects.first().receive_time), "2022-02-06 16:49:05.421398+00:00")


    def test_submit_bad_key(self):

        self.assertEqual(len(Downlink.objects.all()), 0) # downlink table empty

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 200)
        frame = '{ "qos": 98.6, "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66, "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}'

        frame_json = json.loads(frame)
        request_key = self.factory.get(path='members/key/', content_type='application/json')

        user = Member.objects.get(username='user')
        force_authenticate(request_key, user=user)

        request_key.user = user
        generate_key(request_key).content


        request = self.factory.post(path='submit_frame', data=frame_json, content_type='application/json')
        request.user = user
        request.META['HTTP_AUTHORIZATION'] = "qwerty"

        response = submit_frame(request)

        self.assertEquals(response.status_code, 401)
        self.assertEqual(len(Downlink.objects.all()), 0) # dowlink table has no entry
