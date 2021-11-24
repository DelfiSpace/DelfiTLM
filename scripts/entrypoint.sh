#!/bin/sh

set -e

python manage.py collectstatic --noinput

# run a TCP socket
uwsgi --socket :8000 --master --enable-threads --module delfitlm.wsgi
