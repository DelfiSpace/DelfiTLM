"""API request handling. Map requests to the corresponding HTMLs."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from transmission.processing.process_raw_bucket import process_raw_bucket


def process_telemetry(request):
    """Trigger delfi_pq telemetry processing"""
    user = request.user

    if user.has_perm("transmission.view_downlink"):
        processed_frames_count, total_frames_count = process_raw_bucket("delfi_pq","downlink")
        message = f"{processed_frames_count}/{total_frames_count}"
        message += " delfi_pq telemetry frames processed"
        messages.info(request, message)
        return JsonResponse({"message": message})

    return PermissionDenied()
