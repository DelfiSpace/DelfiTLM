"""Transmission app forms"""
from django import forms

satellites = [
    (None, '-'),
    ('delfi_pq', 'Delfi-PQ'),
    ('delfi_c3', 'Delfi-C3'),
    ('delfi_next', 'Delfi-Next'),
    ('da_vinci', 'Da-Vinci-Satellite'),
]

jobs = [
    (None, '-'),
    ('buffer_processing', 'Frame Buffer Processing'),
    ('buffer_reprocessing', 'Frame Buffer Reprocessing'),
    ('scraper', 'Scrape'),
    ('raw_bucket_processing', 'Bucket Processing (new frames)'),
    ('reprocess_failed_raw_bucket', 'Bucket Reprocessing (failed frames)'),
    ('reprocess_entire_raw_bucket', 'Bucket Reprocessing (entire bucket)'),
]

links = [
    (None, '-'),
    ('downlink', 'Downlink'),
    ('uplink', 'Uplink'),
]


class SubmitJob(forms.Form):
    """Job submission form"""

    sat = forms.ChoiceField(choices=satellites, widget=forms.Select, label='Satellite [1]', required=False)
    job_type = forms.ChoiceField(choices=jobs, widget=forms.Select, label='Job Type')
    link = forms.ChoiceField(choices=links, widget=forms.Select, label='Link [2]', required=False)
    datetime = forms.DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Run datetime",
        required=False
    )
    interval = forms.IntegerField(min_value=1, label="Time Interval (minutes)", required=False)
