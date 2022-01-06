#!/bin/bash
coverage run --source='.' manage.py test
coverage combine
coverage html
coverage erase