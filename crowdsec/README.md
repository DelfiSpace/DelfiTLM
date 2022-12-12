# CrowdSec

CrowdSec is included as a service in the `docker-compose-deploy.yml`. CrowdSec parses nginx access logs as configured in `crowdsec/acquis.yaml` and checks against a set of scenarios that could indicate an attack is happening. If that is to happen, CrowdSec issues an alert and the bouncer will block that specific IP address. The bouncer polls CrowdSec at a regular interval to obtain the updated list of banned IP addresses and enforces the ban. The exact interval length is configurable.

To access the CrowdSec cli (cscli) run: `docker exec -it delfitlm_crowdsec_1 /bin/bash`.

## Install collections 

Crowdsec Hub can be used to install scenarios under which bans are enforced: https://docs.crowdsec.net/docs/user_guides/hub_mgmt/.

1. Access the container for cscli: `docker exec -it delfitlm_crowdsec_1 /bin/bash`.

2. Install the `nginx` scenario collection: `cscli collections install crowdsecurity/nginx`.

## Create API keys for bouncers

1. Access the container for cscli: `docker exec -it delfitlm_crowdsec_1 /bin/bash`.

2. Create an api key with: `cscli bouncers add BouncerName`. (save it for the firewall setup)

## Firewall bouncer setup

Useful links:
    - https://docs.crowdsec.net/docs/bouncers/firewall/
    - https://prog.world/securing-docker-compose-stacks-with-crowdsec/

1. Create an API key in CrowdSec for the bouncer: `cscli bouncers add HostFirewallBouncer`.

2. Run `./install_bouncer.sh` in the '/scripts' directory to install the bouncer.

3. When given the prompt below, type `iptables`.
   ```
    ptables found
    nftables found
    Found nftables(default) and iptables, which firewall do you want to use (nftables/iptables)?
   ```
4. Open `/etc/crowdsec/cs-firewall-bouncer/cs-firewall-bouncer.yaml` and make sure it has the following contents with and set `the api_url` and `api_key` with appropriate values. The `update_frequency` defines the interval at which the bouncer polls CrowdSec for banned IP addresses.

```
mode: iptables
piddir: /var/run/
update_frequency: 10s
daemonize: true
log_mode: file
log_dir: /var/log/
log_level: info
api_url: http://localhost:8080/
api_key: add-key-here
disable_ipv6: yes
#if present, insert rule in those chains
iptables_chains:
  # - INPUT
  # - FORWARD
  - DOCKER-USER
```

4. Run `./start_bouncer.sh` in the `/scripts` directory to start the firewall bouncer. Poll requests should be visible in the CrowSec logs.


## Pycrowdsec bouncer setup

GitHub and instructions: https://github.com/crowdsecurity/pycrowdsec

This bouncer doesn't require any installs outside docker and can be configured for Django from `settings.py`. Make sure to set the url and the key to the LAPI in the environment variables. Banned IP addresses will be redirected to a `Forbidden 403` view.

```
PYCROWDSEC_LAPI_KEY = os.environ.get('CROWDSEC_LAPI')
PYCROWDSEC_LAPI_URL = os.environ.get('CROWDSEC_URL')

PYCROWDSEC_ACTIONS = {
    "ban": lambda request: redirect(reverse("ban_view")),
}
# IMPORTANT: If any action is doing a redirect to some view, always exclude it for pycrowdsec. Otherwise the middleware will trigger the redirect on the action view too.
PYCROWDSEC_EXCLUDE_VIEWS = {"ban_view"}

PYCROWDSEC_POLL_INTERVAL = 10
```

## CrowdSec Dashboard

System stats and graphs, including the scenarios and bouncers, can be viewed at https://app.crowdsec.net/ upon registering the server.
