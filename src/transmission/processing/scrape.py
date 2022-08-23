"""Scrape satnogs"""
# pylint: disable=E0401
from transmission.processing.telemetry_scraper import scrape

# Run this file from within the src folder (if ran as a standalone script)

scrape("delfi_pq")
# scrape("delfi_next")
# scrape("delfi_c3")
# scrape("da_vinci")
