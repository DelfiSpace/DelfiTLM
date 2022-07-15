import requests
import re
import time
import json
from datetime import datetime, timedelta
# pylint: disable=all

cookieAuth = open("src/tokens/satnogs_token.txt", "r")

path = "https://db.satnogs.org/api/telemetry/"
headers = {'accept': 'application/json', 'Authorization': 'Token ' + cookieAuth}

now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

print("Now: " + now)

f = open("delfi-pq.txt", "w")
i = 0
telemetry = []
telemetry_tmp = []

while i < 1:
	#params = {'app_source':'network', 'end': now, 'format': 'json', 'satellite': '51074'}
	params = {'end': now, 'format': 'json', 'satellite': '51074'}
	r = requests.get(path, params=params, headers=headers)

	telemetry_tmp = r.json()

	try:
		last = telemetry_tmp[-1]
		last_time = last['timestamp']

		# concatenate telemetry
		telemetry = telemetry + telemetry_tmp

		last_time = datetime.strptime(last['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
		next_time = last_time - timedelta(seconds=1)
		now = next_time.strftime("%Y-%m-%dT%H:%M:%SZ")

		print("Next " + now)

	except IndexError:
		i = 1
	except KeyError:
		print(telemetry_tmp)
		if 'detail' in telemetry_tmp:
			if re.match("throttled\s", telemetry_tmp["detail"]):
				delay = re.findall('[0-9]+', telemetry_tmp["detail"])[0]
				print("Sleeping " + str(delay) + " s (request throttled)")
				time.sleep(int(delay))
			else:
				i = 1
		else:
			i = 1

f.write(json.dumps(telemetry, indent=4, sort_keys=True))
f.close()
