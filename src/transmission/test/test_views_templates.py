"""Test views html templates"""
import json
from django.test import Client, TestCase, RequestFactory
from rest_framework.test import force_authenticate
from django.contrib.auth.models import Permission
from django.contrib.auth import authenticate, login
from django.http import HttpRequest, SimpleCookie
from django.urls import reverse
from transmission.models import Downlink, Satellite, Uplink
from transmission.processing.satellites import SATELLITES
from transmission.processing.save_raw_data import store_frames
from transmission.views import submit_frame, submit_job, modify_scheduler

from members.models import Member
from members.views import generate_key

from django.conf import settings

from unittest.mock import patch


# pylint: disable=all


class TestSchedulerStateChange(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = Member.objects.create_superuser(username='user', email='user@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()

        self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})

        Satellite.objects.create(sat='delfic3', norad_id=1).save()

    def testUnauthorizedRequest(self):
        unauthorized_user = Member.objects.create_user(username='unauthorized_user',
                                                       email='unauthorized_user@email.com', verified=True)
        unauthorized_user.set_password('delfispace4242')
        unauthorized_user.save()

        request = self.factory.post(path='modify_scheduler', content_type='application/json')
        request.user = unauthorized_user
        response = modify_scheduler(request, "start")

        self.assertEqual(response.status_code, 403)

    def testBadRequest(self):
        response = self.client.post(reverse('submit_job'),
                                    {'sat': 'delfi_c3', 'job_type': 'raw_bucket_processing', 'link': 'downlink'},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "running")

        # pause
        response = self.client.get(reverse('modify_scheduler', args=["pause"]), follow=True)
        self.assertEqual(response.status_code, 400)

    @patch("transmission.scheduler.Scheduler.add_job_to_schedule")
    def testInvalidCommand(self, mock_scheduler):
        # submit job
        response = self.client.post(reverse('submit_job'),
                                    {'sat': 'delfi_c3', 'job_type': 'raw_bucket_processing', 'link': 'downlink'},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "running")

        # wrong command
        response = self.client.post(reverse('modify_scheduler', args=["shut"]), follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "running")

    @patch("transmission.scheduler.Scheduler.add_job_to_schedule")
    def testPauseScheduler(self, mock_scheduler):
        # submit job
        response = self.client.post(reverse('submit_job'),
                                    {'sat': 'delfi_c3', 'job_type': 'raw_bucket_processing', 'link': 'downlink'},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "running")

        # pause
        response = self.client.post(reverse('modify_scheduler', args=["pause"]), follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "paused")

        # resume
        response = self.client.post(reverse('modify_scheduler', args=["resume"]), follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "running")

    @patch("transmission.scheduler.Scheduler.add_job_to_schedule")
    def testShutdownScheduler(self, mock_scheduler):
        # submit job
        response = self.client.post(reverse('submit_job'),
                                    {'sat': 'delfi_c3', 'job_type': 'raw_bucket_processing', 'link': 'downlink'},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "running")

        # shutdown
        response = self.client.post(reverse('modify_scheduler', args=["shutdown"]), follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "shutdown")

        # submit again
        response = self.client.post(reverse('submit_job'),
                                    {'sat': 'delfi_c3', 'job_type': 'raw_bucket_processing', 'link': 'downlink'},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "running")

        # force shutdown
        response = self.client.post(reverse('modify_scheduler', args=["force_shutdown"]), follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "shutdown")

        # start again
        response = self.client.post(reverse('modify_scheduler', args=["start"]), follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        scheduler_satus = response.context['scheduler_status']
        self.assertEqual(scheduler_satus, "running")


class TestJobSubmission(TestCase):
    def login_wrapper(self, username, password):
        # create a request to retrieve Axes authentication success of failure
        request = HttpRequest()
        # store the session coookie in the request
        request.session = self.client.session
        # try to authenticate the user
        authenticated_user = authenticate(request, username=username, password=password)

        if authenticated_user is None:
            # authentication failure
            return False, "Username / password not correct"

        if authenticated_user.username != "user":
            # username / password not correct
            return False, "Incorrect user authenticated"

        # login now
        request = HttpRequest()
        request.session = self.client.session
        login(request, authenticated_user)

        # save the session cookie
        request.session.save()
        session_cookie = settings.SESSION_COOKIE_NAME
        self.client.cookies[session_cookie] = request.session.session_key
        cookie_data = {
            "max-age": None,
            "path": "/",
            "domain": settings.SESSION_COOKIE_DOMAIN,
            "secure": settings.SESSION_COOKIE_SECURE or None,
            "expires": None,
        }
        self.client.cookies[session_cookie].update(cookie_data)
        return True, "Success"

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = Member.objects.create_superuser(username='user', email='user@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()

        self.login_wrapper('user', 'delfispace4242')

        Satellite.objects.create(sat='delfic3', norad_id=1).save()

    def testUnauthorizedRequest(self):
        unauthorized_user = Member.objects.create_user(username='unauthorized_user',
                                                       email='unauthorized_user@email.com', verified=True)
        unauthorized_user.set_password('delfispace4242')
        unauthorized_user.save()

        request = self.factory.post(path='submit_job', data={'sat': '', 'job_type': 'scraper', 'link': ''},
                                    content_type='application/json')
        request.user = unauthorized_user
        response = submit_job(request)

        self.assertEqual(response.status_code, 403)

    def testBadFormSubmission(self):
        response = self.client.post(reverse('submit_job'), {'sat': '', 'job_type': 'scraper', 'link': ''}, follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "['Select a satellite and/or link!']")

    @patch("transmission.scheduler.Scheduler.add_job_to_schedule")
    def testBucketProcessingJob(self, mock_scheduler):
        response = self.client.post(reverse('submit_job'), {'sat': '', 'job_type': 'raw_bucket_processing', 'link': ''},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "['Select a satellite and/or link!']")

        response = self.client.post(reverse('submit_job'),
                                    {'sat': 'delfi_c3', 'job_type': 'raw_bucket_processing', 'link': 'downlink'},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertTrue("bucket_processing" in str(messages[0]))

    @patch("transmission.scheduler.Scheduler.add_job_to_schedule")
    def testBucketReprocessingJob(self, mock_scheduler):
        response = self.client.post(reverse('submit_job'),
                                    {'sat': '', 'job_type': 'reprocess_entire_raw_bucket', 'link': ''}, follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "['Select a satellite and/or link!']")

        response = self.client.post(reverse('submit_job'),
                                    {'sat': 'delfi_c3', 'job_type': 'reprocess_entire_raw_bucket', 'link': 'downlink'},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertTrue("reprocess_entire_raw_bucket" in str(messages[0]))

        response = self.client.post(reverse('submit_job'),
                                    {'sat': '', 'job_type': 'reprocess_failed_raw_bucket', 'link': ''}, follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "['Select a satellite and/or link!']")

        response = self.client.post(reverse('submit_job'),
                                    {'sat': 'delfi_c3', 'job_type': 'reprocess_failed_raw_bucket', 'link': 'downlink'},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertTrue("reprocess_failed_raw_bucket" in str(messages[0]))

    @patch("transmission.scheduler.Scheduler.add_job_to_schedule")
    def testScraperJob(self, mock_scheduler):
        response = self.client.post(reverse('submit_job'), {'sat': '', 'job_type': 'scraper', 'link': ''}, follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "['Select a satellite and/or link!']")

        response = self.client.post(reverse('submit_job'),
                                    {'sat': 'delfi_c3', 'job_type': 'scraper', 'link': 'downlink'}, follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertTrue("scraper" in str(messages[0]))

    @patch("transmission.scheduler.Scheduler.add_job_to_schedule")
    def testBufferProcessingJob(self, mock_scheduler):
        response = self.client.post(reverse('submit_job'), {'sat': '', 'job_type': 'buffer_processing', 'link': '', 'user': 'user'},
                                    follow=True)

        self.assertTemplateUsed(response, 'transmission/submit_job.html')
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertTrue("buffer_processing" in str(messages[0]))


class TestTableViews(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = Member.objects.create_superuser(username='user', email='user@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.user.save()
        Satellite.objects.create(sat='delfic3', norad_id=1).save()

    def tearDown(self):
        self.client.logout()

    def test_requested_tables(self):
        # access uplink/downlink tables
        frame = {"link": "downlink", "qos": 98.6, "sat": "delfic3", "timestamp": "2021-12-19T02:20:14.959630Z",
                 "frequency": 2455.66,
                 "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}
        store_frames(frame, "user")
        frame = {"link": "uplink", "qos": 98.6, "sat": "delfic3", "timestamp": "2021-12-19T02:20:14.959630Z",
                 "frequency": 2455.66,
                 "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}
        store_frames(frame, "user")

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('get_frames_table', args=["downlink"]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('get_frames_table', args=["uplink"]))
        self.assertEqual(response.status_code, 200)

    def test_requested_tables_no_permissions(self):
        # cannot access uplink/downlink tables without proper permission
        # if not logged in, redirect to ligin page
        response = self.client.get(reverse('get_frames_table', args=["downlink"]))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('get_frames_table', args=["uplink"]))
        self.assertEqual(response.status_code, 302)

    def test_requested_tables_bad_requests(self):
        # tables must be requested with a get request
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 302)

        response = self.client.delete(reverse('get_frames_table', args=["downlink"]))
        self.assertEqual(response.status_code, 400)

        response = self.client.post(reverse('get_frames_table', args=["uplink"]))
        self.assertEqual(response.status_code, 400)


class TestSubmitFrames(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = Member.objects.create_user(username='user', email='user@email.com', verified=True)
        self.user.set_password('delfispace4242')
        self.add_downlink_permission = Permission.objects.get(codename='add_downlink')
        self.add_uplink_permission = Permission.objects.get(codename='add_uplink')
        self.user.user_permissions.add(self.add_downlink_permission)
        self.user.user_permissions.add(self.add_uplink_permission)
        self.user.save()
        Satellite.objects.create(sat='delfic3', norad_id=1).save()

    def tearDown(self):
        self.client.logout()

    def test_submit_get_request_not_allowed(self):

        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty

        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 302)

        request = self.factory.get(path='submit_frame')
        response = submit_frame(request)

        self.assertEqual(response.status_code, 405)

    def test_submit_invalid_json(self):

        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty

        frame = '{ "qos": 98.6 "timestamp": "2021-12-19T02:20:14.959630Z" "frequency": 2455.66 "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}'

        request_key = self.factory.get(path='members/key/', content_type='application/json')

        user = Member.objects.get(username='user')
        force_authenticate(request_key, user=user)

        request_key.user = user
        response_key = generate_key(request_key).content

        request = self.factory.post(path='submit_frame', data=frame, content_type='application/json')
        request.user = user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']

        response = submit_frame(request)

        self.assertEqual(response.status_code, 400)

    def test_submit_frame_is_not_hex(self):

        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty

        frame = '{ "link": "downlink", "qos": 98.6, "sat": "delfic3", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66, "frame": "foo"}'

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

        self.assertEqual(response.status_code, 400)

    def test_submit_no_timestamps(self):

        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty

        frame = '{ "link": "downlink", "qos": 98.6, "pass": "qwerty", "frequency": 2455.66, "processed": true, "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}'
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

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table has no entry

    def test_submit_with_timestamps(self):

        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty
        self.assertEqual(len(Uplink.objects.all()), 0)  # uplink table empty

        frame_uplink = {"link": "uplink", "qos": 98.6, "sat": "delfic3", "timestamp": "2021-12-19T02:20:14.959630Z",
                        "frequency": 2455.66,
                        "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}
        frame_downlink = {"link": "downlink", "qos": 98.6, "sat": "delfic3", "timestamp": "2021-12-19T02:20:14.959630Z",
                          "frequency": 2455.66,
                          "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}

        request_key = self.factory.get(path='members/key/', content_type='application/json')

        user = Member.objects.get(username='user')
        force_authenticate(request_key, user=user)

        request_key.user = user
        response_key = generate_key(request_key).content

        request = self.factory.post(path='submit_frame', data=frame_downlink, content_type='application/json')
        request.user = user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']

        # test downlink
        response = submit_frame(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Downlink.objects.all()), 1)  # downlink table has 1 entry
        self.assertEqual(str(Downlink.objects.first().timestamp), "2021-12-19 02:20:14.959630+00:00")

        # test uplink
        request = self.factory.post(path='submit_frame', data=frame_uplink, content_type='application/json')
        request.user = user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']

        response = submit_frame(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Uplink.objects.all()), 1)  # uplink table has 1 entry
        self.assertEqual(str(Uplink.objects.first().timestamp), "2021-12-19 02:20:14.959630+00:00")

    def test_submit_with_timestamps(self):

        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty
        self.assertEqual(len(Uplink.objects.all()), 0)  # uplink table empty

        f1 = {"qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F00008730150020002008100400000002D63007DE95A02FF64FFF1FFFF000F0BC3004411B00F990F8A000E03ECFFB3FFC300000000000000240000000000000EB80014FFFF0021000010CD0FE111560EECFF7CFEE0FF65FF0F00080000001000000FA20146104D012C00100000000500000B0001460B3B"}
        f2 = {"qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F000081B015002000300000000000000000000000000000000000000000000"}
        f3 = {"qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F000082801500200040093000E00000000AB0078993702FFEDFC10250027FFDDFF8D011A000000000000FFB4"}

        frame_list = [f1, f2, f3]
        for f in frame_list:
            f["link"] = "downlink"

        request_key = self.factory.get(path='members/key/', content_type='application/json')

        user = Member.objects.get(username='user')
        force_authenticate(request_key, user=user)

        request_key.user = user
        response_key = generate_key(request_key).content

        request = self.factory.post(path='submit_frame', data=frame_list, content_type='application/json')
        request.user = user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']

        # test downlink
        response = submit_frame(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Downlink.objects.all()), 3)  # downlink table has 1 entry

        # test uplink
        frame_list = [f1, f2, f3]
        for f in frame_list:
            f["link"] = "uplink"
        request = self.factory.post(path='submit_frame', data=frame_list, content_type='application/json')
        request.user = user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']

        response = submit_frame(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Uplink.objects.all()), 3)  # uplink table has 1 entry

    def test_submit_with_non_utc_timestamps(self):

        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty

        frame = '{ "link": "downlink","qos": 98.6, "timestamp": "2022-02-06 17:49:05.421398+01:00", "frequency": 2455.66, "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}'

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

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Downlink.objects.all()), 1)  # downlink table has 1 entry
        self.assertEqual(str(Downlink.objects.first().timestamp), "2022-02-06 16:49:05.421398+00:00")

    def test_submit_bad_key(self):

        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty

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

        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table has no entry

    def test_submit_without_permissions(self):

        unauthorized_user = Member.objects.create_user(username='unauthorized_user',
                                                       email='unauthorized_user@email.com', verified=True)
        unauthorized_user.set_password('delfispace4242')
        unauthorized_user.save()

        self.assertEqual(len(Uplink.objects.all()), 0)  # uplink table empty
        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty

        response = self.client.post(reverse('login'), {'username': 'unauthorized_user', 'password': 'delfispace4242'})
        self.assertEqual(response.status_code, 302)
        frame = '{ "qos": 98.6, "sat": "delfic3", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66, "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}'

        frame_json = json.loads(frame)
        request_key = self.factory.get(path='members/key/', content_type='application/json')

        request_key.user = unauthorized_user
        response_key = generate_key(request_key).content

        # UPLINK
        request = self.factory.post(path='submit_frame', data=frame_json, content_type='application/json')
        request.user = unauthorized_user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']
        request.META['HTTP_FRAME_LINK'] = 'uplink'

        response = submit_frame(request)

        self.assertEqual(response.status_code, 403)

        # DOWNLINK
        request = self.factory.post(path='submit_frame', data=frame_json, content_type='application/json')
        request.user = unauthorized_user
        request.META['HTTP_AUTHORIZATION'] = json.loads(response_key)['generated_key']
        request.META['HTTP_FRAME_LINK'] = 'downlink'

        response = submit_frame(request)

        self.assertEqual(response.status_code, 403)

        self.assertEqual(len(Uplink.objects.all()), 0)  # uplink table empty
        self.assertEqual(len(Downlink.objects.all()), 0)  # downlink table empty

    def test_submit_with_invalid_frame_link(self):

        self.assertEqual(len(Uplink.objects.all()), 0)  # uplink table empty

        frame = '{ "link": "foo", "qos": 98.6, "sat": "delfic3", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66, "frame": "A8989A40404000888C9C66B0A80003F0890FFDAD776500001E601983C008C39C10D02911E2F0FF71230DECE70032044C09500311119B8CA092A08B5E85919492938285939C7900000000000000000000005602F637005601F3380000006D70000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434B1345B440BF3C9736D0301D240E000004B82C4050B26DDB942EB4D0CFE4E9D64946"}'

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

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Uplink.objects.all()), 0)
