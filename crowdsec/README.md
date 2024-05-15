# CrowdSec

CrowdSec is included as a service in the `docker-compose-deploy.yml`. CrowdSec parses nginx access logs as configured in `crowdsec/acquis.yaml` and checks against a set of scenarios that could indicate an attack is happening. If that is to happen, CrowdSec issues an alert and the bouncer will block that specific IP address. The bouncer polls CrowdSec at a regular interval to obtain the updated list of banned IP addresses and enforces the ban. The exact interval length is configurable.

To access the CrowdSec cli (cscli) run: `docker exec -it delfitlm_crowdsec_1 /bin/bash`.

## CrowdSec Dashboard

System stats and graphs, including the scenarios and bouncers, can be viewed at https://app.crowdsec.net/ upon registering the server.
Afgter registration, it is required to enroll the search engine in the online console by generating an API KEY. After this has been generated, the API KEY can be registered on the Crowdsec image:

1. Access the container for cscli: `docker exec -it delfitlm_crowdsec_1 /bin/bash`.

2. Enroll the Search Engine: `sudo cscli console enroll <API_KEY>`. 

## Install collections 

Crowdsec Hub can be used to install scenarios under which bans are enforced: https://docs.crowdsec.net/docs/user_guides/hub_mgmt/.
A basic set of collections is already installed in the container but extra collections can be easilly added.

1. Access the container for cscli: `docker exec -it delfitlm_crowdsec_1 /bin/bash`.

2. Install the `nginx` scenario collection: `cscli collections install crowdsecurity/nginx`. This is just an example, as the `nginx` in installed by default.

## Bouncers setup

Crowdsec is used to identify threats and, in case a decision is reached to ban a certain connection, a bouncer is required. This guide covers two bouncers tha can be used but more are available.

The iptables Firewall Bouncer controls the host iptable settings to ban users: this allows to block malicious users from accessing the whole machine, making it a safer option but requiring  to be installed on the host. In case access to the host is possible, this solution is preferable as it protects the whole Docker system and not just few of its containers.

A Python Bouncer can also be installed to protect the Django app: this bouncer does not require any access to the host machine but it only protects the app by banning malicious users to access the `app` container but allowing them to still eventually access all other containers. In terms of security, this solution is inferior to the iptables host Firewall bouncer but it requires no access to the host machine.

Using both bouncers is possible as, anytime Crowdsec will reach a ban decision, both bouncers will be activated both bannng the same connection. Once the iptables Firewall bouncr will have banned a connection, this will never reach the Python bouncer, making it superfluous. <ins>It is thus advised to only use the iptables Firewall Bouncer, whenever possible</ins>.
1. Access the container for cscli: `docker exec -it delfitlm_crowdsec_1 /bin/bash`.

2. Create an api key with: `cscli bouncers add BouncerName`. (save it for the firewall setup)

### Firewall bouncer setup

Useful links:
    - https://docs.crowdsec.net/docs/next/getting_started/install_crowdsec/#intall-our-repositories
    - https://docs.crowdsec.net/docs/bouncers/firewall/
    - https://prog.world/securing-docker-compose-stacks-with-crowdsec/

1. Access the container for cscli: `docker exec -it delfitlm_crowdsec_1 /bin/bash`.
   
2. Create an API key in CrowdSec for the bouncer: `cscli bouncers add HostFirewallBouncer`.

3. Write down the API KEY that has been generated.

Now, access the host machine:

1. Set-up the Crowdsec repository `curl -s https://packagecloud.io/install/repositories/crowdsec/crowdsec/script.deb.sh | sudo bash`.

2. Install the bouncer `sudo apt install crowdsec-firewall-bouncer-iptables`.
 
3. Open `/etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml` and make sure it has the following contents with and set `the api_url` and `api_key` with appropriate values. The `update_frequency` defines the interval at which the bouncer polls CrowdSec for banned IP addresses.

```
mode: iptables
update_frequency: 10s
log_mode: file
log_dir: /var/log/
log_level: info
log_compression: true
log_max_size: 1
log_max_backups: 3
log_max_age: 30
api_url: http://127.0.0.1:8080/
api_key: <add-key-here>
insecure_skip_verify: false
disable_ipv6: true
deny_action: DROP
deny_log: false
supported_decisions_types:
  - ban
#to change the blacklists name
blacklists_ipv4: crowdsec-blacklists
#if present, insert rule in those chains
iptables_chains:
#  - INPUT
#  - FORWARD
  - DOCKER-USER
```

4. Run `sudo systemctl start crowdsec-firewall-bouncer.service` to start the firewall bouncer. Poll requests should be visible in the CrowSec logs.


### Pycrowdsec bouncer setup

GitHub and instructions: https://github.com/crowdsecurity/pycrowdsec

1. Access the container for cscli: `docker exec -it delfitlm_crowdsec_1 /bin/bash`.
   
2. Create an API key in CrowdSec for the bouncer: `cscli bouncers add python_bouncer`.

3. Write down the API KEY that has been generated.

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
## Whitelists

Whitelista are used to ignore machines considered to be safe (such as security scanners) and avoid them to trigger a ban. A guide is available [here](https://docs.crowdsec.net/docs/whitelist/create/). It is reccommended to use the PostOverflows whitelist to limit the amount of events.

To add a whitelist, a file needs to be added to the Docker CrowdSec config volume: it should be noted that deleting the volume will cause the whitelist to be deleted.

This guide applies to Linux, but it can be adapted to any other operating system.

Create a whitelist file in the Docker volume:
```sudo touch /var/lib/docker/volumes/delfitlm_crowdsec_config/_data/postoverflows/s01-whitelist/mywhitelist.yaml ```

Edit the whitelist file just created and paste the following lines, adapting the content:
```
name: <my-domain>/<my-name>
description: "<Description of this whitelist>"
whitelist:
  reason: <Reason for the whitelist>
  ip:
    - "<IP address to whitelist>"
```
Restart the CrowdSec image.

## Email notifications

CrowdSec, with the [email plugin](https://docs.crowdsec.net/docs/notification_plugins/email/) allows to send notifications in case of critical events. Emails are sent in case decisions are taken or errors are detected.



