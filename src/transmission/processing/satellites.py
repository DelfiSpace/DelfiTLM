"""Satellite related constants"""

TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

SATELLITES = {
    "delfi_pq": {
        "norad_id": '51074',
        "status": "Decayed",
        "launch": "2022-01-13T18:00:00.000Z",
    },
    "delfi_next": {
        "norad_id": '39428',
        "status": "Non Operational",
        "launch": "2013-11-21T18:00:00.000Z",
    },
    "delfi_c3": {
        "norad_id": '32789',
        "status": "Decayed",
        "launch": "2008-04-28T18:00:00.000Z",
        },
    "da_vinci": {
       "norad_id": None,  #update id
       "status": "Under Development",
       "launch": None,
    }
}
