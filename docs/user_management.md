---
layout: default
title: User Management
nav_order: 2
---

# User management on the platform

To ensure smooth operation of the satellites, user permissions can be created via the Django Admin interface. In our use case we distinguish three user roles with different sets of permissions, namely:

1. External radio amateur

- in addition to accessing public website information (posts and dashboards view-only), the external radio amateur is also able to generate an API token to submit relevant telemetry data they have received. This process is further detailed in the *How to submit telemetry?* section.

2. Ground station operator

- has the permissions of the external radio amateur and can access to both uplink and downlink data and trigger/schedule data processing tasks. Submitting uplink commands via the radio is also allowed (to be implemented). Since multiple satellites can be managed at once, satellite specific permissions can easily be implemented such that the operators are granted access to each satellite independently.

3. Admin

- this role includes the permissions of the ground station operator with the addition of managing user accounts, granting/revoking user permissions and blocking access from selected accounts via the Django Admin interface.

