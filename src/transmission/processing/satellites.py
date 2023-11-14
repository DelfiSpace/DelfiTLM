"""Satellite related constants"""

TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

SATELLITES = {
    "delfi_pq": {
        "norad_id": '51074',
        "status": "Operational",
    },
    "delfi_next": {
        "norad_id": '39428',
        "status": "Inactive",
    },
    "delfi_c3": {
        "norad_id": '32789',
        "status": "Inactive",
        },
    "da_vinci": {
       "norad_id": None,  #update id
       "status": "Under Development"
    }
}
