"""Transmission app forms"""
from django import forms

class SubmitJob(forms.Form):
    """Job submission form"""
    satellites=[
        ('delfi_pq', 'Delfi-PQ'),
        ('delfi_c3', 'Delfi-C3'),
        ]

    jobs=[
        ('raw_bucket_processing','Bucket Processing'),
        ('scraper', 'Scrape'),
        ]

    links=[
        ('downlink', 'Downlink'),
        ('uplink', 'Uplink'),
        ]

    sat = forms.ChoiceField(choices=satellites, widget=forms.Select, label='Satellite')
    job_type = forms.ChoiceField(choices=jobs, widget=forms.Select, label='Job Type')
    link = forms.ChoiceField(choices=links, widget=forms.Select, label='Link')
