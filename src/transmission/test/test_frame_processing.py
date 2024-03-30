"""Test views html templates"""

from django.test import Client, TestCase, RequestFactory, tag
from django.contrib.messages.storage.fallback import FallbackStorage

from transmission.models import Downlink, Satellite, Uplink
from transmission.processing.satellites import SATELLITES
from transmission.processing.save_raw_data import process_uplink_and_downlink, store_frames
from transmission.views import delete_processed_frames, process

from members.models import Member

from unittest.mock import patch
# pylint: disable=all


class TestFrameSubmission(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = Member.objects.create_superuser(username='user', email='user@email.com')
        self.user.set_password('delfispace4242')

        self.user.save()
        Satellite.objects.create(sat='delfipq', norad_id=1).save()

    def testSubmitFramesBatch(self):
        # add 3 valid frames from delfi_pq
        f1 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F00008730150020002008100400000002D63007DE95A02FF64FFF1FFFF000F0BC3004411B00F990F8A000E03ECFFB3FFC300000000000000240000000000000EB80014FFFF0021000010CD0FE111560EECFF7CFEE0FF65FF0F00080000001000000FA20146104D012C00100000000500000B0001460B3B"}
        f2 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F000081B015002000300000000000000000000000000000000000000000000"}
        f3 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F000082801500200040093000E00000000AB0078993702FFEDFC10250027FFDDFF8D011A000000000000FFB4"}
        frame_list = [f1, f2, f3]

        for f in frame_list:
            f["link"] = "downlink"
        store_frames(frame_list, "user")
        self.assertEqual(len(Downlink.objects.all()), 3)

        for f in frame_list:
            f["link"] = "uplink"
        store_frames(frame_list, "user")
        self.assertEqual(len(Uplink.objects.all()), 3)

    def testSubmitFrameOneByOne(self):
        # add 3 valid frames from delfi_pq
        f1 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F00008730150020002008100400000002D63007DE95A02FF64FFF1FFFF000F0BC3004411B00F990F8A000E03ECFFB3FFC300000000000000240000000000000EB80014FFFF0021000010CD0FE111560EECFF7CFEE0FF65FF0F00080000001000000FA20146104D012C00100000000500000B0001460B3B"}
        f2 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F000081B015002000300000000000000000000000000000000000000000000"}
        f3 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EA49EAA9C88E088988C92A0A26103F000082801500200040093000E00000000AB0078993702FFEDFC10250027FFDDFF8D011A000000000000FFB4"}
        frame_list = [f1, f2, f3]

        for f in frame_list:
            f["link"] = "uplink"
            store_frames(f, "user")

        self.assertEqual(len(Uplink.objects.all()), 3)

class TestFramesProcessing(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = Member.objects.create_superuser(username='user', email='user@email.com')
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
            f["link"] = "downlink"
            store_frames(f, "user")
            f["link"] = "uplink"
            store_frames(f, "user")

    def tearDown(self):
        self.client.logout()


    @patch('transmission.processing.save_raw_data.store_frame_to_influxdb')
    def test_bad_request(self, mock_store_frame_to_influxdb):
        mock_store_frame_to_influxdb.return_value = (True, 'delfi_pq')

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)
        # process frames
        process_uplink_and_downlink()

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)
        # request to delete processed frames
        request = self.factory.get(path='transmission/delete-processed-frames/', content_type='application/json')
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        request.user = self.user

        # bad request
        res = delete_processed_frames(request, "uplink")
        self.assertEqual(res.status_code, 400)

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)


    @patch('transmission.processing.save_raw_data.store_frame_to_influxdb')
    def test_delete_processed_frames(self, mock_store_frame_to_influxdb):
        mock_store_frame_to_influxdb.return_value = (True, 'delfi_pq')

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)
        # process frames
        process_uplink_and_downlink()

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)
        # request to delete processed frames
        request = self.factory.post(path='transmission/delete-processed-frames/', content_type='application/json')
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        request.user = self.user

        # invalid link
        res = delete_processed_frames(request, "foo")
        self.assertEqual(res.status_code, 400)

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)

        res = delete_processed_frames(request, "uplink")
        self.assertEqual(res.status_code, 302)

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 0)

        res = delete_processed_frames(request, "downlink")

        # frames were successfully removed
        self.assertEqual(len(Downlink.objects.all()), 0)
        self.assertEqual(len(Uplink.objects.all()), 0)
        self.assertEqual(res.status_code, 302)


    @patch('transmission.processing.save_raw_data.store_frame_to_influxdb')
    def test_delete_no_processed_frames(self, mock_store_frame_to_influxdb):
        mock_store_frame_to_influxdb.return_value = (False, None)

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)

        process_uplink_and_downlink()

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)

        # try to delete frames without processing them
        request = self.factory.post(path='transmission/delete-processed-frames/', content_type='application/json')
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        request.user = self.user

        delete_processed_frames(request, "uplink")
        delete_processed_frames(request, "downlink")

        # no frames are removed
        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)


    @patch('transmission.processing.save_raw_data.store_frame_to_influxdb')
    def test_delete_processed_frames_without_permissions(self, mock_store_frame_to_influxdb):
        unauthorized_user = Member.objects.create_user(username='unauthorized_user', email='unauthorized_user@email.com')
        unauthorized_user.set_password('delfispace4242')
        unauthorized_user.save()

        mock_store_frame_to_influxdb.return_value = (True, 'delfi_pq')
        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)

        process_uplink_and_downlink()

        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)

        # try to delete frames without proper rights
        request = self.factory.post(path='transmission/delete-processed-frames/', content_type='application/json')
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        request.user = unauthorized_user
        delete_processed_frames(request, "uplink")
        delete_processed_frames(request, "downlink")

        # no frames are removed
        self.assertEqual(len(Downlink.objects.all()), 3)
        self.assertEqual(len(Uplink.objects.all()), 3)

    @patch('transmission.processing.save_raw_data.store_frame_to_influxdb')
    def test_frames_processing_request(self, mock_store_frame_to_influxdb):

        mock_store_frame_to_influxdb.return_value = (True, "delfi_pq")
        # request to process frames
        request = self.factory.post(path='transmission/process-frames/', content_type='application/json')
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        request.user = self.user

        self.assertEqual(len(Downlink.objects.all().filter(processed=False)), 3)
        self.assertEqual(len(Uplink.objects.all().filter(processed=False)), 3)

        res = process(request, "uplink")
        self.assertEqual(res.status_code, 302)
        res = process(request, "downlink")
        self.assertEqual(res.status_code, 302)

        # frames successfully processed
        self.assertEqual(len(Downlink.objects.all().filter(processed=True)), 3)
        self.assertEqual(len(Uplink.objects.all().filter(processed=True)), 3)


    @patch('transmission.processing.save_raw_data.store_frame_to_influxdb')
    def test_frames_processing_request_bad_request(self, mock_store_frame_to_influxdb):

        mock_store_frame_to_influxdb.return_value = (True, 'delfi_pq')
        request = self.factory.post(path='transmission/process-frames/', content_type='application/json')
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        request.user = self.user

        self.assertEqual(len(Downlink.objects.all().filter(processed=False)), 3)
        self.assertEqual(len(Uplink.objects.all().filter(processed=False)), 3)

        # invalid link, bad request
        res = process(request, "foo")
        self.assertEqual(res.status_code, 400)
        # no frames are processed
        self.assertEqual(len(Downlink.objects.all().filter(processed=True)), 0)
        self.assertEqual(len(Uplink.objects.all().filter(processed=True)), 0)


    @patch('transmission.processing.save_raw_data.store_frame_to_influxdb')
    def test_frames_processing_request_forbidden(self, mock_store_frame_to_influxdb):

        mock_store_frame_to_influxdb.return_value = (True, 'delfi_pq')

        unauthorized_user = Member.objects.create_user(username='unauthorized_user', email='unauthorized_user@email.com')
        unauthorized_user.set_password('delfispace4242')
        unauthorized_user.save()

        request = self.factory.post(path='transmission/process-frames/', content_type='application/json')
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        request.user = unauthorized_user

        self.assertEqual(len(Downlink.objects.all().filter(processed=False)), 3)
        self.assertEqual(len(Uplink.objects.all().filter(processed=False)), 3)

        # unauthorized user cannot process frames
        res = process(request, "uplink")
        self.assertEqual(res.status_code, 403)
        # no frames are processed
        self.assertEqual(len(Downlink.objects.all().filter(processed=True)), 0)
        self.assertEqual(len(Uplink.objects.all().filter(processed=True)), 0)

    @tag('XMLRequired')
    @patch('transmission.processing.influxdb_api.commit_frame')
    @patch('transmission.processing.influxdb_api.save_raw_frame_to_influxdb')
    def test_valid_frames_processing(self, mock_commit_frame, mock_save_raw_frame_to_influxdb):
        mock_save_raw_frame_to_influxdb.return_value = (True, 'delfi_pq')
        mock_commit_frame.return_value = True

        request = self.factory.post(path='transmission/process-frames/', content_type='application/json')
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        request.user = self.user

        self.assertEqual(len(Downlink.objects.all().filter(processed=False)), 3)
        self.assertEqual(len(Uplink.objects.all().filter(processed=False)), 3)
        # ok request
        res = process(request, "uplink")
        self.assertEqual(res.status_code, 302)
        res = process(request, "downlink")
        self.assertEqual(res.status_code, 302)
        # frames are successfully processed
        self.assertEqual(len(Downlink.objects.all().filter(processed=True)), 3)
        self.assertEqual(len(Uplink.objects.all().filter(processed=True)), 3)
        # no invalid frames detected
        self.assertEqual(len(Downlink.objects.all().filter(invalid=True)), 0)
        self.assertEqual(len(Uplink.objects.all().filter(invalid=True)), 0)

    @tag('XMLRequired')
    @patch('transmission.processing.influxdb_api.commit_frame')
    @patch('transmission.processing.influxdb_api.save_raw_frame_to_influxdb')
    def test_invalid_frames_processing(self, mock_commit_frame, mock_save_raw_frame_to_influxdb):
        mock_save_raw_frame_to_influxdb.return_value = (True, 'delfi_pq')
        mock_commit_frame.return_value = True

        request = self.factory.post(path='transmission/process-frames/', content_type='application/json')
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        request.user = self.user

        # add 3 invalid frames
        f1 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EB49EAA9C88E088988C92A0A26103F00008730150020002008100400000002D63007DE95A02FF64FFF1FFFF000F0BC3004411B00F990F8A000E03ECFFB3FFC300000000000000240000000000000EB80014FFFF0021000010CD0FE111560EECFF7CFEE0FF65FF0F00080000001000000FA20146104D012C00100000000500000B0001460B3B"}
        f2 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EB49EAA9C88E088988C92A0A26103F000081B015002000300000000000000000000000000000000000000000000"}
        f3 = { "qos": 98.6, "sat": "delfipq", "timestamp": "2021-12-19T02:20:14.959630Z", "frequency": 2455.66,
              "frame": "8EB49EAA9C88E088988C92A0A26103F000082801500200040093000E00000000AB0078993702FFEDFC10250027FFDDFF8D011A000000000000FFB4"}

        for f in [f1, f2, f3]:
            f["link"] = "downlink"
            store_frames(f, "user")
            f["link"] = "uplink"
            store_frames(f, "user")

        # there are 3 valid and 3 invalid frames
        self.assertEqual(len(Downlink.objects.all().filter(processed=False)), 6)
        self.assertEqual(len(Uplink.objects.all().filter(processed=False)), 6)

        # processing request is successful
        res = process(request, "uplink")
        self.assertEqual(res.status_code, 302)
        res = process(request, "downlink")
        self.assertEqual(res.status_code, 302)

        # 3 frames get processed
        self.assertEqual(len(Downlink.objects.all().filter(processed=True)), 3)
        self.assertEqual(len(Uplink.objects.all().filter(processed=True)), 3)
        # 3 frames are marked as invalid
        self.assertEqual(len(Downlink.objects.all().filter(invalid=True)), 3)
        self.assertEqual(len(Uplink.objects.all().filter(invalid=True)), 3)
